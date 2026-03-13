"""Поиск игр и локальных хранилищ данных на системном диске."""

import json
import os
import re
import winreg
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GameInfo:
    name: str
    launcher: str          # "Steam" | "Epic Games" | "GOG"
    install_path: str
    size_bytes: int

    @property
    def drive(self) -> str:
        return self.install_path[:2].upper() if len(self.install_path) >= 2 else ""


@dataclass
class VaultInfo:
    """Локальное хранилище приложения, требующего ручного переноса."""
    name: str        # имя папки / хранилища
    app: str         # "Obsidian"
    path: str        # полный путь
    size_bytes: int  # 0 если не удалось посчитать


# ─── VDF-парсер ───────────────────────────────────────────────────────────────

def _parse_vdf(text: str) -> dict:
    """
    Минимальный рекурсивный парсер Valve Data Format (KeyValues).
    Возвращает вложенный dict; все ключи приведены к нижнему регистру.
    """
    result: dict = {}
    stack: list[dict] = [result]
    pending_key: str | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line == "{":
            if pending_key is not None:
                child: dict = {}
                stack[-1][pending_key] = child
                stack.append(child)
                pending_key = None
        elif line == "}":
            if len(stack) > 1:
                stack.pop()
        else:
            tokens = re.findall(r'"((?:[^"\\]|\\.)*)"', line)
            if len(tokens) >= 2:
                stack[-1][tokens[0].lower()] = tokens[1].replace("\\\\", "\\")
            elif len(tokens) == 1:
                pending_key = tokens[0].lower()

    return result


# ─── Steam ────────────────────────────────────────────────────────────────────

def _steam_root() -> Path | None:
    """Ищет корневую папку Steam через реестр, затем через стандартные пути."""
    candidates = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamPath"),
    ]
    for hive, path, key in candidates:
        try:
            with winreg.OpenKey(hive, path) as k:
                val, _ = winreg.QueryValueEx(k, key)
                p = Path(val)
                if p.exists():
                    return p
        except OSError:
            pass
    for fallback in [
        Path("C:/Program Files (x86)/Steam"),
        Path("C:/Program Files/Steam"),
    ]:
        if fallback.exists():
            return fallback
    return None


def _scan_steam(drive: str) -> list[GameInfo]:
    steam = _steam_root()
    if not steam:
        return []

    vdf_path = steam / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        return []

    try:
        parsed = _parse_vdf(vdf_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []

    # Извлекаем пути библиотек (поддерживаем и старый и новый формат VDF)
    library_paths: list[Path] = []
    root = parsed.get("libraryfolders", parsed)
    for _k, val in root.items():
        if isinstance(val, dict):
            p = val.get("path", "")
            if p:
                library_paths.append(Path(p))
        elif isinstance(val, str) and len(val) >= 2 and val[1] == ":":
            library_paths.append(Path(val))

    drive_pfx = drive.upper().rstrip("\\/")
    games: list[GameInfo] = []

    for lib in library_paths:
        if not str(lib).upper().startswith(drive_pfx):
            continue
        steamapps = lib / "steamapps"
        if not steamapps.exists():
            continue
        for acf in steamapps.glob("appmanifest_*.acf"):
            try:
                data = _parse_vdf(
                    acf.read_text(encoding="utf-8", errors="replace")
                ).get("appstate", {})
                name = data.get("name", "")
                installdir = data.get("installdir", "")
                size = int(data.get("sizeondisk", 0))
                if not name or not installdir:
                    continue
                games.append(GameInfo(
                    name=name,
                    launcher="Steam",
                    install_path=str(steamapps / "common" / installdir),
                    size_bytes=size,
                ))
            except Exception:
                pass

    return games


# ─── Epic Games Store ─────────────────────────────────────────────────────────

def _scan_epic(drive: str) -> list[GameInfo]:
    manifests_dir = Path("C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")
    if not manifests_dir.exists():
        return []

    drive_pfx = drive.upper().rstrip("\\/")
    games: list[GameInfo] = []

    for item_file in manifests_dir.glob("*.item"):
        try:
            data = json.loads(item_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if data.get("bIsIncompleteInstall"):
            continue
        if data.get("IsDlc") or data.get("bIsDlc"):
            continue

        name = data.get("DisplayName", "")
        location = data.get("InstallLocation", "")
        size = data.get("InstallSize", 0)

        if not name or not location:
            continue
        if not location.upper().startswith(drive_pfx):
            continue

        games.append(GameInfo(
            name=name,
            launcher="Epic Games",
            install_path=location,
            size_bytes=size,
        ))

    return games


# ─── GOG Galaxy ───────────────────────────────────────────────────────────────

def _scan_gog(drive: str) -> list[GameInfo]:
    drive_pfx = drive.upper().rstrip("\\/")
    games: list[GameInfo] = []

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games"),
    ]

    for hive, path in reg_paths:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue

        count = winreg.QueryInfoKey(root)[0]
        for i in range(count):
            try:
                sub_name = winreg.EnumKey(root, i)
                sub = winreg.OpenKey(root, sub_name)
                try:
                    # DLC имеют DEPENDENCYGAMEID — пропускаем
                    winreg.QueryValueEx(sub, "DEPENDENCYGAMEID")
                    sub.Close()
                    continue
                except OSError:
                    pass

                def _rv(k, field):
                    try:
                        v, _ = winreg.QueryValueEx(k, field)
                        return v
                    except OSError:
                        return ""

                name = _rv(sub, "GAMENAME")
                install_path = _rv(sub, "PATH")
                sub.Close()

                if name and install_path and install_path.upper().startswith(drive_pfx):
                    games.append(GameInfo(
                        name=name,
                        launcher="GOG",
                        install_path=install_path,
                        size_bytes=0,   # реестр GOG не хранит точный размер
                    ))
            except Exception:
                pass

        root.Close()
        if games:
            break  # нашли в первом пути, не ищем дальше

    return games


# ─── Публичный API ────────────────────────────────────────────────────────────

# ─── Obsidian vaults ──────────────────────────────────────────────────────────

def _dir_size_fast(path: Path) -> int:
    """Быстрый подсчёт размера папки (рекурсивно, с перехватом ошибок)."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += _dir_size_fast(Path(entry.path))
            except OSError:
                pass
    except OSError:
        pass
    return total


def scan_obsidian_vaults(system_drive: str = "C:") -> list[VaultInfo]:
    """
    Читает %APPDATA%\\obsidian\\obsidian.json и возвращает хранилища
    (vaults), расположенные на system_drive.
    """
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return []

    config_path = Path(appdata) / "obsidian" / "obsidian.json"
    if not config_path.exists():
        return []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    vaults_raw = data.get("vaults", {})
    drive_pfx = system_drive.upper().rstrip("\\/")
    results: list[VaultInfo] = []

    for _vault_id, vault_data in vaults_raw.items():
        path_str = vault_data.get("path", "")
        if not path_str or not path_str.upper().startswith(drive_pfx):
            continue
        p = Path(path_str)
        size = _dir_size_fast(p) if p.exists() else 0
        results.append(VaultInfo(
            name=p.name,
            app="Obsidian",
            path=path_str,
            size_bytes=size,
        ))

    return results


def scan_games_on_system_drive(system_drive: str = "C:") -> list[GameInfo]:
    """
    Возвращает список игр, установленных на системном диске.
    Сканирует Steam, Epic Games Store и GOG Galaxy.
    Результат отсортирован по убыванию размера (крупные игры — первыми).
    """
    games: list[GameInfo] = []
    for scanner in (_scan_steam, _scan_epic, _scan_gog):
        try:
            games.extend(scanner(system_drive))
        except Exception:
            pass

    # Дедупликация по имени (Steam + GOG могут задвоить одну игру)
    seen: set[str] = set()
    unique: list[GameInfo] = []
    for g in games:
        if g.name not in seen:
            seen.add(g.name)
            unique.append(g)

    return sorted(unique, key=lambda g: (-g.size_bytes, g.name.lower()))

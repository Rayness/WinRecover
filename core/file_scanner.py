"""Поиск конфигов и личных файлов."""

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {
    "temp", "tmp", "cache", "crashreports", "crashes", "logs",
    "d3dscache", "gpucache", "code cache", "shader cache",
    "service worker", "webcache",
}

# Расширения файлов-конфигов
CONFIG_EXTENSIONS = {
    ".json", ".ini", ".cfg", ".conf", ".config", ".xml", ".yaml", ".yml",
    ".toml", ".properties", ".reg", ".prefs", ".plist",
    ".db", ".sqlite", ".sqlite3", ".ldb", ".leveldb",
}

PERSONAL_EXTENSIONS = {
    ".doc", ".docx", ".pdf", ".txt", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".raw",
    ".mp4", ".avi", ".mov", ".mkv",
    ".mp3", ".flac", ".wav",
    ".zip", ".rar", ".7z",
}

PERSONAL_FOLDERS = ["Documents", "Pictures", "Videos", "Music", "Downloads"]

# Словарь известных приложений: имя папки (lower) -> (priority, reason)
# priority: "important" — рекомендуем сохранить, "skip" — можно пропустить
KNOWN_APPS: dict[str, tuple[str, str]] = {
    # Важные — сохранить
    "code":                  ("important", "Настройки VS Code"),
    "code - insiders":       ("important", "Настройки VS Code Insiders"),
    "cursor":                ("important", "Настройки Cursor IDE"),
    "discord":               ("important", "Настройки Discord"),
    "telegram desktop":      ("important", "Настройки Telegram"),
    "slack":                 ("important", "Настройки Slack"),
    "notepad++":             ("important", "Настройки Notepad++"),
    "obs-studio":            ("important", "Настройки OBS Studio"),
    "keepass":               ("important", "База паролей KeePass"),
    "keepass2":              ("important", "База паролей KeePass"),
    "filezilla":             ("important", "Настройки FileZilla"),
    "simontatham":           ("important", "Настройки PuTTY"),
    "sublime text":          ("important", "Настройки Sublime Text"),
    "sublime text 3":        ("important", "Настройки Sublime Text"),
    "mozilla":               ("important", "Профиль Firefox"),
    "jetbrains":             ("important", "Настройки JetBrains IDE"),
    "ghisler":               ("important", "Настройки Total Commander"),
    "everything":            ("important", "Настройки Everything"),
    "mpv":                   ("important", "Настройки mpv"),
    "mpvnet":                ("important", "Настройки mpvnet"),
    "vlc":                   ("important", "Настройки VLC"),
    "git":                   ("important", "Настройки Git"),
    "winrar":                ("important", "Настройки WinRAR"),
    "7-zip":                 ("important", "Настройки 7-Zip"),
    "postman":               ("important", "Настройки Postman"),
    "dbeaver":               ("important", "Настройки DBeaver"),
    "heidisql":              ("important", "Настройки HeidiSQL"),
    "insomnia":              ("important", "Настройки Insomnia"),
    "fork":                  ("important", "Настройки Fork (Git-клиент)"),
    "gitkraken":             ("important", "Настройки GitKraken"),
    "tableplus":             ("important", "Настройки TablePlus"),
    "bitwarden":             ("important", "Настройки Bitwarden"),
    "authy":                 ("important", "Настройки Authy (2FA)"),
    "windirstat":            ("important", "Настройки WinDirStat"),
    "sharex":                ("important", "Настройки ShareX"),
    "autohotkey":            ("important", "Скрипты AutoHotkey"),
    "terminal":              ("important", "Настройки Windows Terminal"),
    "blender foundation":    ("important", "Настройки, аддоны и пользовательские данные Blender"),
    "blender":               ("important", "Настройки, аддоны и пользовательские данные Blender"),
    "hydra-launcher":        ("important", "Библиотека и настройки Hydra Launcher"),
    "hydra launcher":        ("important", "Библиотека и настройки Hydra Launcher"),
    "hydra":                 ("important", "Библиотека и настройки Hydra Launcher"),
    "vortex":                ("important", "Профили и настройки Vortex (менеджер модов)"),
    "antigravity":           ("important", "Данные и настройки Antigravity"),

    # VPN / Proxy клиенты — конфиги и подписки важны
    "flclash":               ("important", "Конфиги и подписки FLClash"),
    "flclashx":              ("important", "Конфиги и подписки FLClashX"),
    "clash":                 ("important", "Конфиги и подписки Clash"),
    "clashverge":            ("important", "Конфиги и подписки Clash Verge"),
    "clash verge":           ("important", "Конфиги и подписки Clash Verge"),
    "clashx":                ("important", "Конфиги и подписки ClashX"),
    "v2rayn":                ("important", "Конфиги и подписки v2rayN"),
    "v2ray":                 ("important", "Конфиги и подписки v2ray"),
    "xray":                  ("important", "Конфиги и подписки Xray"),
    "nekoray":               ("important", "Конфиги и подписки Nekoray"),
    "hiddify":               ("important", "Конфиги и подписки Hiddify"),
    "shadowsocks":           ("important", "Конфиги и подписки Shadowsocks"),
    "proxifier":             ("important", "Профили и правила Proxifier"),
    "wireguard":             ("important", "Ключи и конфиги WireGuard"),
    "openvpn":               ("important", "Профили OpenVPN"),

    # Пропустить — восстанавливается автоматически
    "nvidia corporation":    ("skip", "Кэш NVIDIA — восстанавливается автоматически"),
    "amd":                   ("skip", "Кэш AMD — восстанавливается автоматически"),
    "microsoft":             ("skip", "Системные папки Windows"),
    "packages":              ("skip", "Пакеты Windows Store — скачиваются заново"),
    "steam":                 ("skip", "Steam — синхронизируется через облако"),
    "epic games":            ("skip", "Epic Games — синхронизируется через аккаунт"),
    "google":                ("skip", "Google-приложения — синхронизируются через аккаунт"),
    "battle.net":            ("skip", "Battle.net — синхронизируется"),
    "ubisoft":               ("skip", "Ubisoft Connect — синхронизируется"),
    "ea desktop":            ("skip", "EA App — синхронизируется"),
    "rockstar games":        ("skip", "Rockstar — синхронизируется"),
    "intel":                 ("skip", "Данные Intel — восстанавливаются автоматически"),
    "crashreporter":         ("skip", "Отчёты об ошибках — не нужны"),
    "squirrel":              ("skip", "Установщик Squirrel — не нужен"),
    "cef cache":             ("skip", "Кэш браузерного движка"),
}


def _get_priority(name: str) -> tuple[str, str]:
    """Возвращает (priority, reason) для папки по имени."""
    lower = name.lower()
    if lower in KNOWN_APPS:
        return KNOWN_APPS[lower]
    # Частичное совпадение для JetBrains (CLion, PyCharm, IDEA, ...)
    for key, val in KNOWN_APPS.items():
        if key in lower or lower in key:
            return val
    return ("", "")


@dataclass
class ChildEntry:
    """Дочерний элемент папки (первый уровень)."""
    name: str
    is_dir: bool
    size: int


@dataclass
class FoundItem:
    """Найденный элемент."""
    name: str
    path: Path
    relative_path: str
    is_dir: bool
    size: int
    item_type: str  # "config" или "personal"
    content_type: str = ""  # "config" / "other" / "" — тип содержимого
    children: list[ChildEntry] = field(default_factory=list)
    location: str = ""    # "Local" / "Roaming" / ""
    priority: str = ""    # "important" / "skip" / ""
    priority_reason: str = ""  # Пояснение к рекомендации


def _classify_dir(path: Path) -> tuple[str, list[ChildEntry]]:
    """
    Определяет тип содержимого папки и собирает список дочерних элементов.
    Возвращает (content_type, children).
    """
    children: list[ChildEntry] = []
    has_config_files = False
    try:
        for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            try:
                if entry.is_dir():
                    # Для подпапок считаем только приблизительный размер (быстро)
                    size = 0
                    try:
                        # Считаем только файлы первого уровня внутри подпапки
                        for sub in entry.iterdir():
                            if sub.is_file():
                                try:
                                    size += sub.stat().st_size
                                except OSError:
                                    pass
                    except (OSError, PermissionError):
                        pass
                    children.append(ChildEntry(name=entry.name, is_dir=True, size=size))
                elif entry.is_file():
                    try:
                        size = entry.stat().st_size
                    except OSError:
                        size = 0
                    children.append(ChildEntry(name=entry.name, is_dir=False, size=size))
                    if entry.suffix.lower() in CONFIG_EXTENSIONS:
                        has_config_files = True
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass

    content_type = "config" if has_config_files else "other"
    return content_type, children


def _dir_size(path: Path, timeout_sec: float = 5.0) -> int:
    """Рекурсивно считает размер директории с таймаутом."""
    total = 0
    start = time.time()
    file_count = 0
    try:
        for entry in path.rglob("*"):
            if time.time() - start > timeout_sec:
                logger.warning(
                    "  [_dir_size] ТАЙМАУТ %.1fс для '%s' (файлов: %d, размер пока: %d)",
                    timeout_sec, path.name, file_count, total,
                )
                return total
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError) as e:
        logger.warning("  [_dir_size] Ошибка доступа к '%s': %s", path, e)
    elapsed = time.time() - start
    if elapsed > 1.0:
        logger.info("  [_dir_size] '%s' — %d файлов, %d байт за %.1fс", path.name, file_count, total, elapsed)
    return total


def scan_appdata(
    username: str,
    progress_callback: Callable[[str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[FoundItem]:
    """Сканирует AppData на наличие конфигов программ."""
    logger.info("=" * 60)
    logger.info("[scan_appdata] НАЧАЛО сканирования для пользователя '%s'", username)
    results: list[FoundItem] = []
    user_dir = Path(os.environ.get("USERPROFILE", f"C:\\Users\\{username}"))
    appdata_dirs = [
        user_dir / "AppData" / "Local",
        user_dir / "AppData" / "Roaming",
    ]

    scan_start = time.time()

    for appdata in appdata_dirs:
        location = appdata.name  # "Local" или "Roaming"
        logger.info("[scan_appdata] Сканирую: %s", appdata)
        if not appdata.exists():
            logger.warning("[scan_appdata] Папка не существует: %s", appdata)
            continue
        try:
            entries = sorted(appdata.iterdir())
            logger.info("[scan_appdata] Найдено %d записей в %s", len(entries), appdata.name)
        except PermissionError as e:
            logger.error("[scan_appdata] Нет доступа к %s: %s", appdata, e)
            continue

        for i, entry in enumerate(entries):
            if cancel_check and cancel_check():
                logger.info("[scan_appdata] ОТМЕНА сканирования")
                return results
            if not entry.is_dir():
                continue
            if entry.name.lower() in EXCLUDED_DIRS:
                logger.debug("[scan_appdata] Пропущена исключённая папка: %s", entry.name)
                continue

            if progress_callback:
                progress_callback(str(entry))

            logger.info("[scan_appdata] [%d/%d] Считаю размер: %s", i + 1, len(entries), entry.name)
            dir_start = time.time()
            size = _dir_size(entry)
            dir_elapsed = time.time() - dir_start

            if size < 1024:
                logger.debug("[scan_appdata]   -> пропущено (размер %d < 1024), %.2fс", size, dir_elapsed)
                continue

            # Классифицируем содержимое и собираем дочерние элементы
            content_type, children = _classify_dir(entry)
            priority, priority_reason = _get_priority(entry.name)

            logger.info("[scan_appdata]   -> НАЙДЕНО: %s, размер=%d, тип=%s, loc=%s, prior=%s, детей=%d, время=%.2fс",
                        entry.name, size, content_type, location, priority, len(children), dir_elapsed)
            rel = str(entry.relative_to(user_dir))
            results.append(FoundItem(
                name=entry.name,
                path=entry,
                relative_path=rel,
                is_dir=True,
                size=size,
                item_type="config",
                content_type=content_type,
                children=children,
                location=location,
                priority=priority,
                priority_reason=priority_reason,
            ))

    total_elapsed = time.time() - scan_start
    logger.info("[scan_appdata] ЗАВЕРШЕНО: найдено %d конфигов за %.1fс", len(results), total_elapsed)
    logger.info("=" * 60)
    return results


def scan_personal_files(
    username: str,
    progress_callback: Callable[[str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[FoundItem]:
    """Сканирует личные файлы пользователя."""
    logger.info("=" * 60)
    logger.info("[scan_personal] НАЧАЛО сканирования личных файлов")
    results: list[FoundItem] = []
    user_dir = Path(os.environ.get("USERPROFILE", f"C:\\Users\\{username}"))
    scan_start = time.time()

    for folder_name in PERSONAL_FOLDERS:
        folder = user_dir / folder_name
        if not folder.exists():
            logger.info("[scan_personal] Папка не существует: %s", folder)
            continue

        logger.info("[scan_personal] Сканирую папку: %s", folder)
        folder_start = time.time()
        folder_count = 0

        try:
            for entry in folder.rglob("*"):
                if cancel_check and cancel_check():
                    logger.info("[scan_personal] ОТМЕНА сканирования")
                    return results
                if not entry.is_file():
                    continue
                if entry.suffix.lower() not in PERSONAL_EXTENSIONS:
                    continue

                if progress_callback:
                    progress_callback(str(entry))

                try:
                    size = entry.stat().st_size
                except (OSError, PermissionError):
                    continue

                folder_count += 1
                rel = str(entry.relative_to(user_dir))
                results.append(FoundItem(
                    name=entry.name,
                    path=entry,
                    relative_path=rel,
                    is_dir=False,
                    size=size,
                    item_type="personal",
                ))
        except (PermissionError, OSError) as e:
            logger.warning("[scan_personal] Ошибка доступа к %s: %s", folder, e)

        folder_elapsed = time.time() - folder_start
        logger.info("[scan_personal] %s — найдено %d файлов за %.1fс", folder_name, folder_count, folder_elapsed)

    total_elapsed = time.time() - scan_start
    logger.info("[scan_personal] ЗАВЕРШЕНО: найдено %d файлов за %.1fс", len(results), total_elapsed)
    logger.info("=" * 60)
    return results


def scan_ssh_keys() -> list[FoundItem]:
    """
    Сканирует SSH-ключи и конфиги в ~/.ssh/.
    Возвращает список FoundItem с priority=important.
    """
    ssh_dir = Path.home() / ".ssh"
    if not ssh_dir.exists():
        return []

    # Важные файлы — ключи, конфиги, known_hosts
    _IMPORTANT = {
        "id_rsa", "id_rsa.pub",
        "id_ed25519", "id_ed25519.pub",
        "id_ecdsa", "id_ecdsa.pub",
        "id_dsa", "id_dsa.pub",
        "config", "known_hosts", "authorized_keys",
    }

    results: list[FoundItem] = []
    user_dir = Path.home()

    try:
        for f in sorted(ssh_dir.iterdir(), key=lambda x: x.name.lower()):
            if not f.is_file():
                continue
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            try:
                rel = str(f.relative_to(user_dir))
            except ValueError:
                rel = str(f)

            is_known = f.name in _IMPORTANT
            is_key = (
                f.suffix in (".pem", ".ppk", ".key")
                or (not f.suffix and f.name.startswith("id_"))
            )
            if not (is_known or is_key):
                continue  # Пропускаем посторонние файлы в ~/.ssh

            results.append(FoundItem(
                name=f.name,
                path=f,
                relative_path=rel,
                is_dir=False,
                size=size,
                item_type="config",
                content_type="config",
                children=[],
                location="SSH",
                priority="important",
                priority_reason="SSH-ключ / конфиг — нужен для доступа к серверам и GitHub",
            ))
    except (PermissionError, OSError) as e:
        logger.warning("[scan_ssh] Ошибка доступа к %s: %s", ssh_dir, e)

    logger.info("[scan_ssh] Найдено SSH-файлов: %d", len(results))
    return results

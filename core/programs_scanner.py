"""Сканирование установленных программ через реестр Windows."""

import winreg
from dataclasses import dataclass


_UNINSTALL_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]

# Категории в порядке отображения
CATEGORIES_ORDER = [
    "🔧 Драйверы",
    "📦 Системные",
    "🏢 Microsoft",
    "🌐 Браузеры",
    "🎮 Игры и лаунчеры",
    "💻 Разработка",
    "🎵 Медиа",
    "🔒 Безопасность",
    "📄 Офис",
    "📁 Прочее",
]


@dataclass
class ProgramInfo:
    name: str
    publisher: str = ""
    version: str = ""
    install_date: str = ""   # формат YYYYMMDD или пусто
    category: str = "📁 Прочее"

    @property
    def install_date_fmt(self) -> str:
        """Читаемая дата установки (DD.MM.YYYY или пусто)."""
        d = self.install_date
        if len(d) == 8 and d.isdigit():
            return f"{d[6:8]}.{d[4:6]}.{d[:4]}"
        return d


def _detect_category(name: str, publisher: str) -> str:
    nl = name.lower()
    pl = publisher.lower()

    # Системные компоненты (в первую очередь — многие от Microsoft)
    if any(k in nl for k in [
        "redistributable", " runtime", "directx", "visual c++",
        "vcredist", ".net framework", ".net desktop runtime", ".net core",
        "windows sdk", "openal", "physx", "xna framework", "xinput",
        "webview2", "c++ build tools", "build tools for visual studio",
    ]):
        return "📦 Системные"

    # Драйверы
    _driver_publishers = {
        "nvidia", "advanced micro devices", "realtek semiconductor",
        "qualcomm", "broadcom", "marvell", "via technologies",
        "synaptics", "alps electric", "elan microelectronics",
        "american megatrends", "asrock", "asus", "gigabyte",
    }
    is_driver_pub = any(dp in pl for dp in _driver_publishers)
    is_driver_name = any(k in nl for k in [
        "driver", "geforce", "radeon", "hd graphics", "iris xe",
        "chipset", "sata ahci", "usb controller", "graphics card",
    ])
    # Intel — только если явно «driver/graphics», иначе может быть разработка
    if "intel" in pl and is_driver_name:
        is_driver_pub = True
    if is_driver_name or (is_driver_pub and any(k in nl for k in [
        "driver", "graphics", "audio", "network", "wireless", "bluetooth",
        "chipset", "display", "utility", "software", "component", "manager",
    ])):
        return "🔧 Драйверы"

    # Microsoft (после системных и драйверов)
    if "microsoft" in pl:
        return "🏢 Microsoft"

    # Браузеры
    if any(k in nl for k in [
        "google chrome", "firefox", " opera", "brave", "vivaldi",
        "tor browser", "yandex browser", "яндекс", "browser",
        "chromium", "waterfox", "pale moon",
    ]):
        return "🌐 Браузеры"

    # Игры и лаунчеры
    if any(k in nl for k in [
        "steam", "epic games", "gog galaxy", "battle.net", "ubisoft connect",
        "ea app", "ea desktop", "origin", "xbox", "game pass", "playnite",
        "rockstar games", "bethesda", "twitch",
    ]):
        return "🎮 Игры и лаунчеры"
    if any(p in pl for p in [
        "valve", "epic games", "gog.com", "blizzard", "ubisoft", "electronic arts",
        "2k games", "activision",
    ]):
        return "🎮 Игры и лаунчеры"

    # Разработка
    if any(k in nl for k in [
        "visual studio 20", "vs code", "visual studio code",
        "pycharm", "intellij", "webstorm", "phpstorm", "rider",
        "clion", "datagrip", "android studio", "eclipse", "netbeans",
        "git ", "git for windows", "node.js", "python 3", "python 3.",
        "jdk", "java development kit", "docker", "postman", "insomnia",
        "putty", "winscp", "virtualbox", "vmware workstation", "vagrant",
        "cmake", "mingw", "cygwin", "wsl",
    ]):
        return "💻 Разработка"
    if any(p in pl for p in [
        "jetbrains", "oracle corporation", "the git development community",
    ]):
        return "💻 Разработка"

    # Медиа и творчество
    if any(k in nl for k in [
        "vlc", "media player", "spotify", "itunes", "audacity",
        "handbrake", "obs studio", "kdenlive", "davinci resolve",
        "adobe ", "gimp", "inkscape", "blender",
        "foobar2000", "winamp", "aimp", "potplayer", "mpc-",
    ]):
        return "🎵 Медиа"

    # Безопасность / VPN / Proxy
    if any(k in nl for k in [
        "kaspersky", "avast", "avira", "malwarebytes", "bitdefender",
        "eset", "norton", "mcafee", "vpn", "antivirus", "firewall",
        "антивирус", "total security", "internet security",
        # Proxy/tunnel клиенты
        "clash", "v2ray", "xray", "shadowsocks", "trojan", "mihomo",
        "nekoray", "hiddify", "sing-box", "singbox", "proxifier",
        "outline", "wireguard", "openvpn", "tunnelbear",
        "expressvpn", "nordvpn", "surfshark", "protonvpn",
    ]):
        return "🔒 Безопасность"

    # Офис
    if any(k in nl for k in [
        "libreoffice", "openoffice", "wps office",
        "microsoft office", "office 365",
    ]):
        return "📄 Офис"

    return "📁 Прочее"


def _reg_value(key, name):
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return value
    except OSError:
        return None


def scan_installed_programs() -> list[ProgramInfo]:
    """
    Читает реестр и возвращает список установленных программ.
    Дубликаты (одно приложение в 32- и 64-битной ветке) объединяются по имени.
    """
    seen: dict[str, ProgramInfo] = {}

    for hive, path in _UNINSTALL_PATHS:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue

        count = winreg.QueryInfoKey(root)[0]
        for i in range(count):
            try:
                sub_name = winreg.EnumKey(root, i)
                sub = winreg.OpenKey(root, sub_name)
            except OSError:
                continue

            try:
                name = _reg_value(sub, "DisplayName")
                if not name or not name.strip():
                    continue

                # Пропускаем компоненты Windows и обновления
                if _reg_value(sub, "SystemComponent") == 1:
                    continue
                if _reg_value(sub, "ReleaseType") in ("Update", "Hotfix"):
                    continue
                if name.startswith(("KB", "Security Update", "Update for")):
                    continue

                name = name.strip()
                if name not in seen:
                    publisher = (_reg_value(sub, "Publisher") or "").strip()
                    seen[name] = ProgramInfo(
                        name=name,
                        publisher=publisher,
                        version=(_reg_value(sub, "DisplayVersion") or "").strip(),
                        install_date=(_reg_value(sub, "InstallDate") or "").strip(),
                        category=_detect_category(name, publisher),
                    )
            except Exception:
                pass
            finally:
                sub.Close()

        root.Close()

    return sorted(seen.values(), key=lambda p: p.name.lower())


def programs_to_markdown(programs: list[ProgramInfo]) -> str:
    """Генерирует Markdown-файл со списком программ, сгруппированных по категориям."""
    from collections import defaultdict
    by_cat: dict[str, list[ProgramInfo]] = defaultdict(list)
    for p in programs:
        by_cat[p.category].append(p)

    lines = [
        "# Список установленных программ\n",
        f"_Всего: {len(programs)} программ_\n",
    ]

    def _cat_sort(c: str) -> str:
        try:
            return str(CATEGORIES_ORDER.index(c)).zfill(2)
        except ValueError:
            return "99"

    for cat in sorted(by_cat.keys(), key=_cat_sort):
        entries = by_cat[cat]
        lines += ["", f"## {cat}\n",
                  "| Программа | Издатель | Версия | Дата установки |",
                  "|-----------|----------|--------|----------------|"]
        for p in sorted(entries, key=lambda x: x.name.lower()):
            date = p.install_date_fmt or "—"
            pub = (p.publisher or "—").replace("|", "\\|")
            ver = p.version or "—"
            name_e = p.name.replace("|", "\\|")
            lines.append(f"| {name_e} | {pub} | {ver} | {date} |")

    return "\n".join(lines) + "\n"

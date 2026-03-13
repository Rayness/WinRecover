"""Экран рекомендуемого ПО для чистой установки Windows."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from utils.i18n import tr, get_language


# ─── Данные: (название_ru, название_en, описание_ru, описание_en, url) ─────────
# Структура: list[tuple[cat_ru, cat_en, list[tuple[name, desc_ru, desc_en, url]]]]

# (cat_ru, cat_en, [(name, desc_ru, desc_en, url), ...])
_REC_DATA: list[tuple[str, str, list[tuple[str, str, str, str]]]] = [
    ("🔧 Твики и настройка Windows", "🔧 Windows Tweaks & Setup", [
        ("PowerToys",
         "Microsoft — FancyZones, PowerRename, Color Picker, Peek и ещё десятки утилит",
         "Microsoft — FancyZones, PowerRename, Color Picker, Peek and dozens more utilities",
         "https://github.com/microsoft/PowerToys/releases"),
        ("WinToys",
         "Удобный графический интерфейс для системных твиков и настроек Windows",
         "Friendly GUI for system tweaks and Windows settings",
         "https://apps.microsoft.com/detail/9p8ltpgcbzxd"),
        ("Windhawk",
         "Система модов для Windows — меняет поведение системных компонентов",
         "Windows mod system — changes behavior of system components",
         "https://windhawk.net"),
        ("Winaero Tweaker",
         "Тонкая настройка скрытых параметров Windows",
         "Fine-tune hidden Windows settings",
         "https://winaero.com/winaero-tweaker"),
        ("O&O ShutUp10++",
         "Отключение телеметрии, слежки и ненужных служб одним кликом",
         "Disable telemetry, tracking and unnecessary services in one click",
         "https://www.oo-software.com/en/shutup10"),
        ("Chris Titus Tech WinUtil",
         "Скрипт для быстрой настройки, дебловатинга и установки ПО",
         "Script for quick setup, debloating and software installation",
         "https://github.com/ChrisTitusTech/winutil"),
        ("Optimizer",
         "Твики производительности, приватности и отключения фоновых служб",
         "Performance, privacy tweaks and background service disabling",
         "https://github.com/hellzerg/optimizer"),
    ]),
    ("🎨 Кастомизация интерфейса", "🎨 UI Customization", [
        ("TranslucentTB",
         "Прозрачная / размытая панель задач с гибкими правилами",
         "Transparent / blurred taskbar with flexible rules",
         "https://github.com/TranslucentTB/TranslucentTB"),
        ("ExplorerPatcher",
         "Возврат классического интерфейса Проводника и панели задач",
         "Restore classic Explorer and taskbar interface",
         "https://github.com/valinet/ExplorerPatcher"),
        ("StartAllBack",
         "Полная кастомизация меню Пуск и панели задач (платная, ~3$)",
         "Full Start menu and taskbar customization (paid, ~$3)",
         "https://www.startallback.com"),
        ("EarTrumpet",
         "Удобное управление громкостью отдельно для каждого приложения",
         "Per-app volume control with a clean UI",
         "https://eartrumpet.app"),
        ("ModernFlyouts",
         "Современные всплывающие панели громкости / яркости",
         "Modern volume/brightness flyout panels",
         "https://modernflyouts-community.github.io"),
        ("Rainmeter",
         "Виджеты и информационные панели на рабочем столе",
         "Desktop widgets and information panels",
         "https://www.rainmeter.net"),
        ("Lively Wallpaper",
         "Живые обои — видео, веб-страницы, анимации",
         "Live wallpapers — videos, web pages, animations",
         "https://www.rocksdanister.com/lively"),
    ]),
    ("🔍 Файлы и поиск", "🔍 Files & Search", [
        ("Everything",
         "Мгновенный поиск любого файла на диске — незаменимый инструмент",
         "Instant search for any file on disk — an indispensable tool",
         "https://www.voidtools.com"),
        ("WizTree",
         "Анализ занятого места на диске, быстрее WinDirStat",
         "Disk space analyzer, faster than WinDirStat",
         "https://diskanalyzer.com"),
        ("Files",
         "Современный файловый менеджер с вкладками (Microsoft Store)",
         "Modern tabbed file manager (Microsoft Store)",
         "https://files.community"),
        ("Total Commander",
         "Двухпанельный файловый менеджер с богатым функционалом",
         "Dual-pane file manager with rich functionality",
         "https://www.ghisler.com"),
        ("Bulk Rename Utility",
         "Массовое переименование файлов по шаблонам и регулярным выражениям",
         "Batch file renaming with templates and regex",
         "https://www.bulkrenameutility.co.uk"),
    ]),
    ("📦 Архивы", "📦 Archives", [
        ("7-Zip",
         "Бесплатный архиватор с отличной степенью сжатия, поддержка всех форматов",
         "Free archiver with excellent compression, supports all formats",
         "https://www.7-zip.org"),
        ("WinRAR",
         "Проверенный архиватор, особенно полезен для .rar архивов",
         "Proven archiver, especially useful for .rar archives",
         "https://www.rarlab.com"),
    ]),
    ("✏️ Редакторы и заметки", "✏️ Editors & Notes", [
        ("Notepad++",
         "Расширенный текстовый редактор с подсветкой синтаксиса и плагинами",
         "Advanced text editor with syntax highlighting and plugins",
         "https://notepad-plus-plus.org"),
        ("Obsidian",
         "Заметки в Markdown с локальным хранением и мощным поиском",
         "Markdown notes with local storage and powerful search",
         "https://obsidian.md"),
        ("Notion",
         "Онлайн-пространство для заметок, задач и документов",
         "Online workspace for notes, tasks and documents",
         "https://www.notion.so"),
        ("Typora",
         "Чистый Markdown-редактор с режимом живого предпросмотра (платный, ~15$)",
         "Clean Markdown editor with live preview mode (paid, ~$15)",
         "https://typora.io"),
    ]),
    ("💻 Разработка", "💻 Development", [
        ("VS Code",
         "Лёгкий и расширяемый редактор кода от Microsoft",
         "Lightweight and extensible code editor by Microsoft",
         "https://code.visualstudio.com"),
        ("Git for Windows",
         "Git с bash-терминалом — базовый инструмент разработчика",
         "Git with bash terminal — a developer's essential",
         "https://git-scm.com/download/win"),
        ("Windows Terminal",
         "Современный терминал с вкладками, поддержкой WSL и PowerShell",
         "Modern tabbed terminal with WSL and PowerShell support",
         "https://github.com/microsoft/terminal/releases"),
        ("Node.js (LTS)",
         "JavaScript runtime — нужен для большинства фронтенд-проектов",
         "JavaScript runtime — required for most frontend projects",
         "https://nodejs.org"),
        ("Python",
         "Язык общего назначения, популярен в скриптинге и автоматизации",
         "General-purpose language, popular for scripting and automation",
         "https://www.python.org/downloads"),
        ("WSL2",
         "Linux-окружение прямо в Windows — незаменимо для веб-разработки",
         "Linux environment inside Windows — essential for web development",
         "https://learn.microsoft.com/en-us/windows/wsl/install"),
        ("Docker Desktop",
         "Контейнеризация для локальной разработки и тестирования",
         "Containerization for local development and testing",
         "https://www.docker.com/products/docker-desktop"),
        ("Postman",
         "Тестирование REST и GraphQL API",
         "REST and GraphQL API testing",
         "https://www.postman.com/downloads"),
        ("DBeaver",
         "Универсальный клиент для баз данных (MySQL, PostgreSQL, SQLite...)",
         "Universal database client (MySQL, PostgreSQL, SQLite...)",
         "https://dbeaver.io/download"),
        ("Fork",
         "Быстрый и удобный графический клиент для Git",
         "Fast and friendly Git GUI client",
         "https://git-fork.com"),
    ]),
    ("🔒 Безопасность и приватность", "🔒 Security & Privacy", [
        ("Bitwarden",
         "Бесплатный менеджер паролей с облачной синхронизацией — open source",
         "Free open-source password manager with cloud sync",
         "https://bitwarden.com/download"),
        ("KeePassXC",
         "Локальный менеджер паролей без облака",
         "Local password manager without cloud dependency",
         "https://keepassxc.org/download"),
        ("Malwarebytes",
         "Сканер вредоносных программ — полезен для разовой проверки",
         "Malware scanner — useful for one-time checks",
         "https://www.malwarebytes.com"),
        ("WireGuard",
         "Быстрый и современный VPN-протокол",
         "Fast and modern VPN protocol",
         "https://www.wireguard.com/install"),
        ("ProtonVPN",
         "VPN с бесплатным тарифом от создателей ProtonMail",
         "VPN with a free tier from the creators of ProtonMail",
         "https://protonvpn.com/download"),
    ]),
    ("🌐 Браузеры", "🌐 Browsers", [
        ("Firefox",
         "Независимый браузер с сильной приватностью и расширениями",
         "Independent browser with strong privacy and extensions",
         "https://www.mozilla.org/firefox/new"),
        ("Brave",
         "Chromium-браузер со встроенной блокировкой рекламы и трекеров",
         "Chromium browser with built-in ad and tracker blocking",
         "https://brave.com/download"),
        ("Google Chrome",
         "Самый популярный браузер, хорошая совместимость",
         "The most popular browser, great compatibility",
         "https://www.google.com/chrome"),
    ]),
    ("🎵 Медиа и скриншоты", "🎵 Media & Screenshots", [
        ("VLC",
         "Универсальный медиаплеер — воспроизводит всё без кодеков",
         "Universal media player — plays everything without extra codecs",
         "https://www.videolan.org/vlc"),
        ("foobar2000",
         "Лёгкий и мощный аудиоплеер с полной кастомизацией",
         "Lightweight and powerful audio player with full customization",
         "https://www.foobar2000.org"),
        ("OBS Studio",
         "Запись экрана и стриминг, бесплатный и мощный",
         "Screen recording and streaming, free and powerful",
         "https://obsproject.com"),
        ("ShareX",
         "Скриншоты, запись, аннотации, загрузка — всё в одном",
         "Screenshots, recording, annotations, uploads — all in one",
         "https://getsharex.com"),
        ("Spotify",
         "Стриминг музыки",
         "Music streaming",
         "https://www.spotify.com/download"),
        ("MPC-HC",
         "Лёгкий видеоплеер для требовательных пользователей",
         "Lightweight video player for power users",
         "https://github.com/clsid2/mpc-hc/releases"),
        ("mpv",
         "Минималистичный видеоплеер с мощными возможностями",
         "Minimalist video player with powerful capabilities",
         "https://mpv.io"),
    ]),
    ("🎮 Игры", "🎮 Gaming", [
        ("Steam",
         "Основная платформа для PC-игр",
         "The primary platform for PC gaming",
         "https://store.steampowered.com/about"),
        ("GOG Galaxy",
         "DRM-free игры + агрегатор всех лаунчеров в одном интерфейсе",
         "DRM-free games + aggregator for all launchers in one UI",
         "https://www.gog.com/galaxy"),
        ("Epic Games Launcher",
         "Игры Epic + бесплатные игры каждую неделю",
         "Epic games + free games every week",
         "https://store.epicgames.com/download"),
        ("Playnite",
         "Единый лаунчер для всех игр из разных платформ — open source",
         "Unified launcher for all games across platforms — open source",
         "https://playnite.link"),
        ("Hydra Launcher",
         "Агрегатор игровых библиотек с открытым исходным кодом",
         "Open-source game library aggregator",
         "https://github.com/hydralauncher/hydra"),
    ]),
    ("⚙️ Мониторинг и диагностика", "⚙️ Monitoring & Diagnostics", [
        ("HWiNFO",
         "Детальный мониторинг всего железа в реальном времени",
         "Detailed real-time monitoring of all hardware",
         "https://www.hwinfo.com/download"),
        ("CPU-Z",
         "Подробная информация о процессоре, памяти и материнской плате",
         "Detailed info about CPU, memory and motherboard",
         "https://www.cpuid.com/softwares/cpu-z.html"),
        ("GPU-Z",
         "Подробная информация о видеокарте",
         "Detailed information about your GPU",
         "https://www.techpowerup.com/gpuz"),
        ("CrystalDiskInfo",
         "Мониторинг здоровья дисков (S.M.A.R.T.)",
         "Disk health monitoring (S.M.A.R.T.)",
         "https://crystalmark.info/en/software/crystaldiskinfo"),
        ("Process Hacker / System Informer",
         "Продвинутый диспетчер задач с детальной информацией о процессах",
         "Advanced task manager with detailed process information",
         "https://systeminformer.sourceforge.io"),
        ("MSI Afterburner",
         "Разгон и мониторинг видеокарты, OSD-оверлей в играх",
         "GPU overclocking, monitoring and in-game OSD overlay",
         "https://www.msi.com/Landing/afterburner/graphics-cards"),
    ]),
    ("🤖 Автоматизация", "🤖 Automation", [
        ("AutoHotkey",
         "Скрипты для автоматизации действий, горячие клавиши, макросы",
         "Scripts for automating actions, hotkeys, macros",
         "https://www.autohotkey.com"),
        ("PowerAutomate Desktop",
         "Автоматизация рутинных задач от Microsoft (встроен в Windows 11)",
         "Automate routine tasks from Microsoft (built into Windows 11)",
         "https://www.microsoft.com/power-platform/products/power-automate"),
        ("Keypirinha",
         "Быстрый лаунчер и командная строка для Windows",
         "Fast launcher and command palette for Windows",
         "https://keypirinha.com"),
    ]),
]


# ─── Виджет ───────────────────────────────────────────────────────────────────

class RecommendationsScreen(QWidget):
    """Экран со списком рекомендуемого ПО для чистой установки Windows."""

    def __init__(self, on_back: callable, parent=None):
        super().__init__(parent)
        self._build(on_back)

    def _build(self, on_back: callable):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Шапка ────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("screenHeader")
        header.setStyleSheet("#screenHeader { background: #1e1e2e; border-bottom: 1px solid #313244; }")
        header_lo = QHBoxLayout(header)
        header_lo.setContentsMargins(16, 12, 16, 12)

        btn_back = QPushButton(tr("rec.btn_back"))
        btn_back.setProperty("cssClass", "flat")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(on_back)
        header_lo.addWidget(btn_back)

        title_lbl = QLabel(tr("rec.title"))
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_lo.addWidget(title_lbl, 1, Qt.AlignCenter)

        header_lo.addSpacing(btn_back.sizeHint().width())
        root.addWidget(header)

        # ── Прокручиваемый контент ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_lo = QVBoxLayout(content)
        content_lo.setContentsMargins(32, 20, 32, 20)
        content_lo.setSpacing(16)

        hint = QLabel(tr("rec.hint"))
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "muted")
        content_lo.addWidget(hint)

        en = get_language() == "en"
        for cat_ru, cat_en, items in _REC_DATA:
            title = cat_en if en else cat_ru
            localized = [(name, desc_en if en else desc_ru, url)
                         for name, desc_ru, desc_en, url in items]
            content_lo.addWidget(self._build_section(title, localized))

        content_lo.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _build_section(self, title: str, items: list[tuple[str, str, str]]) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #313244;
                border-radius: 8px;
                background: #1e1e2e;
            }
        """)
        lo = QVBoxLayout(frame)
        lo.setContentsMargins(14, 10, 14, 12)
        lo.setSpacing(6)

        # Заголовок категории
        hdr = QLabel(title)
        hdr.setStyleSheet("font-size: 14px; font-weight: bold; border: none; padding-bottom: 4px;")
        lo.addWidget(hdr)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #313244;")
        sep.setFixedHeight(1)
        lo.addWidget(sep)

        for name, desc, url in items:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Название + ссылка
            name_col = QVBoxLayout()
            name_col.setSpacing(1)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                "font-weight: bold; font-size: 13px; border: none;"
            )
            name_col.addWidget(name_lbl)

            if url:
                link_lbl = QLabel(f'<a href="{url}" style="color:#89b4fa; font-size:11px;">{url}</a>')
                link_lbl.setOpenExternalLinks(False)
                link_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
                link_lbl.setStyleSheet("border: none;")
                link_lbl.linkActivated.connect(
                    lambda href: QDesktopServices.openUrl(QUrl(href))
                )
                name_col.addWidget(link_lbl)

            name_widget = QWidget()
            name_widget.setLayout(name_col)
            name_widget.setFixedWidth(280)
            name_widget.setStyleSheet("background: transparent;")
            row.addWidget(name_widget)

            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setProperty("cssClass", "muted")
            desc_lbl.setStyleSheet("border: none;")
            desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row.addWidget(desc_lbl, 1)

            lo.addLayout(row)

        return frame

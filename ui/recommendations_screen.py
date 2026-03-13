"""Экран рекомендуемого ПО для чистой установки Windows."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices


# ─── Данные: (название, описание, url | "") ────────────────────────────────────

RECOMMENDATIONS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("🔧 Твики и настройка Windows", [
        ("PowerToys",                "Microsoft — FancyZones, PowerRename, Color Picker, Peek и ещё десятки утилит",
         "https://github.com/microsoft/PowerToys/releases"),
        ("WinToys",                  "Удобный графический интерфейс для системных твиков и настроек Windows",
         "https://apps.microsoft.com/detail/9p8ltpgcbzxd"),
        ("Windhawk",                 "Система модов для Windows — меняет поведение системных компонентов",
         "https://windhawk.net"),
        ("Winaero Tweaker",          "Тонкая настройка скрытых параметров Windows",
         "https://winaero.com/winaero-tweaker"),
        ("O&O ShutUp10++",           "Отключение телеметрии, слежки и ненужных служб одним кликом",
         "https://www.oo-software.com/en/shutup10"),
        ("Chris Titus Tech WinUtil", "Скрипт для быстрой настройки, дебловатинга и установки ПО",
         "https://github.com/ChrisTitusTech/winutil"),
        ("Optimizer",                "Твики производительности, приватности и отключения фоновых служб",
         "https://github.com/hellzerg/optimizer"),
    ]),
    ("🎨 Кастомизация интерфейса", [
        ("TranslucentTB",            "Прозрачная / размытая панель задач с гибкими правилами",
         "https://github.com/TranslucentTB/TranslucentTB"),
        ("ExplorerPatcher",          "Возврат классического интерфейса Проводника и панели задач",
         "https://github.com/valinet/ExplorerPatcher"),
        ("StartAllBack",             "Полная кастомизация меню Пуск и панели задач (платная, ~3$)",
         "https://www.startallback.com"),
        ("EarTrumpet",               "Удобное управление громкостью отдельно для каждого приложения",
         "https://eartrumpet.app"),
        ("ModernFlyouts",            "Современные всплывающие панели громкости / яркости",
         "https://modernflyouts-community.github.io"),
        ("Rainmeter",                "Виджеты и информационные панели на рабочем столе",
         "https://www.rainmeter.net"),
        ("Lively Wallpaper",         "Живые обои — видео, веб-страницы, анимации",
         "https://www.rocksdanister.com/lively"),
    ]),
    ("🔍 Файлы и поиск", [
        ("Everything",               "Мгновенный поиск любого файла на диске — незаменимый инструмент",
         "https://www.voidtools.com"),
        ("WizTree",                  "Анализ занятого места на диске, быстрее WinDirStat",
         "https://diskanalyzer.com"),
        ("Files",                    "Современный файловый менеджер с вкладками (Microsoft Store)",
         "https://files.community"),
        ("Total Commander",          "Двухпанельный файловый менеджер с богатым функционалом",
         "https://www.ghisler.com"),
        ("Bulk Rename Utility",      "Массовое переименование файлов по шаблонам и регулярным выражениям",
         "https://www.bulkrenameutility.co.uk"),
    ]),
    ("📦 Архивы", [
        ("7-Zip",                    "Бесплатный архиватор с отличной степенью сжатия, поддержка всех форматов",
         "https://www.7-zip.org"),
        ("WinRAR",                   "Проверенный архиватор, особенно полезен для .rar архивов",
         "https://www.rarlab.com"),
    ]),
    ("✏️ Редакторы и заметки", [
        ("Notepad++",                "Расширенный текстовый редактор с подсветкой синтаксиса и плагинами",
         "https://notepad-plus-plus.org"),
        ("Obsidian",                 "Заметки в Markdown с локальным хранением и мощным поиском",
         "https://obsidian.md"),
        ("Notion",                   "Онлайн-пространство для заметок, задач и документов",
         "https://www.notion.so"),
        ("Typora",                   "Чистый Markdown-редактор с режимом живого предпросмотра (платный, ~15$)",
         "https://typora.io"),
    ]),
    ("💻 Разработка", [
        ("VS Code",                  "Лёгкий и расширяемый редактор кода от Microsoft",
         "https://code.visualstudio.com"),
        ("Git for Windows",          "Git с bash-терминалом — базовый инструмент разработчика",
         "https://git-scm.com/download/win"),
        ("Windows Terminal",         "Современный терминал с вкладками, поддержкой WSL и PowerShell",
         "https://github.com/microsoft/terminal/releases"),
        ("Node.js (LTS)",            "JavaScript runtime — нужен для большинства фронтенд-проектов",
         "https://nodejs.org"),
        ("Python",                   "Язык общего назначения, популярен в скриптинге и автоматизации",
         "https://www.python.org/downloads"),
        ("WSL2",                     "Linux-окружение прямо в Windows — незаменимо для веб-разработки",
         "https://learn.microsoft.com/ru-ru/windows/wsl/install"),
        ("Docker Desktop",           "Контейнеризация для локальной разработки и тестирования",
         "https://www.docker.com/products/docker-desktop"),
        ("Postman",                  "Тестирование REST и GraphQL API",
         "https://www.postman.com/downloads"),
        ("DBeaver",                  "Универсальный клиент для баз данных (MySQL, PostgreSQL, SQLite...)",
         "https://dbeaver.io/download"),
        ("Fork",                     "Быстрый и удобный графический клиент для Git",
         "https://git-fork.com"),
    ]),
    ("🔒 Безопасность и приватность", [
        ("Bitwarden",                "Бесплатный менеджер паролей с облачной синхронизацией — open source",
         "https://bitwarden.com/download"),
        ("KeePassXC",                "Локальный менеджер паролей без облака",
         "https://keepassxc.org/download"),
        ("Malwarebytes",             "Сканер вредоносных программ — полезен для разовой проверки",
         "https://www.malwarebytes.com"),
        ("WireGuard",                "Быстрый и современный VPN-протокол",
         "https://www.wireguard.com/install"),
        ("ProtonVPN",                "VPN с бесплатным тарифом от создателей ProtonMail",
         "https://protonvpn.com/download"),
    ]),
    ("🌐 Браузеры", [
        ("Firefox",                  "Независимый браузер с сильной приватностью и расширениями",
         "https://www.mozilla.org/ru/firefox/new"),
        ("Brave",                    "Chromium-браузер со встроенной блокировкой рекламы и трекеров",
         "https://brave.com/download"),
        ("Google Chrome",            "Самый популярный браузер, хорошая совместимость",
         "https://www.google.com/chrome"),
    ]),
    ("🎵 Медиа и скриншоты", [
        ("VLC",                      "Универсальный медиаплеер — воспроизводит всё без кодеков",
         "https://www.videolan.org/vlc"),
        ("foobar2000",               "Лёгкий и мощный аудиоплеер с полной кастомизацией",
         "https://www.foobar2000.org"),
        ("OBS Studio",               "Запись экрана и стриминг, бесплатный и мощный",
         "https://obsproject.com"),
        ("ShareX",                   "Скриншоты, запись, аннотации, загрузка — всё в одном",
         "https://getsharex.com"),
        ("Spotify",                  "Стриминг музыки",
         "https://www.spotify.com/download"),
        ("MPC-HC",                   "Лёгкий видеоплеер для требовательных пользователей",
         "https://github.com/clsid2/mpc-hc/releases"),
        ("mpv",                      "Минималистичный видеоплеер с мощными возможностями",
         "https://mpv.io"),
    ]),
    ("🎮 Игры", [
        ("Steam",                    "Основная платформа для PC-игр",
         "https://store.steampowered.com/about"),
        ("GOG Galaxy",               "DRM-free игры + агрегатор всех лаунчеров в одном интерфейсе",
         "https://www.gog.com/galaxy"),
        ("Epic Games Launcher",      "Игры Epic + бесплатные игры каждую неделю",
         "https://store.epicgames.com/ru/download"),
        ("Playnite",                 "Единый лаунчер для всех игр из разных платформ — open source",
         "https://playnite.link"),
        ("Hydra Launcher",           "Агрегатор игровых библиотек с открытым исходным кодом",
         "https://github.com/hydralauncher/hydra"),
    ]),
    ("⚙️ Мониторинг и диагностика", [
        ("HWiNFO",                   "Детальный мониторинг всего железа в реальном времени",
         "https://www.hwinfo.com/download"),
        ("CPU-Z",                    "Подробная информация о процессоре, памяти и материнской плате",
         "https://www.cpuid.com/softwares/cpu-z.html"),
        ("GPU-Z",                    "Подробная информация о видеокарте",
         "https://www.techpowerup.com/gpuz"),
        ("CrystalDiskInfo",          "Мониторинг здоровья дисков (S.M.A.R.T.)",
         "https://crystalmark.info/en/software/crystaldiskinfo"),
        ("Process Hacker / System Informer", "Продвинутый диспетчер задач с детальной информацией о процессах",
         "https://systeminformer.sourceforge.io"),
        ("MSI Afterburner",          "Разгон и мониторинг видеокарты, OSD-оверлей в играх",
         "https://www.msi.com/Landing/afterburner/graphics-cards"),
    ]),
    ("🤖 Автоматизация", [
        ("AutoHotkey",               "Скрипты для автоматизации действий, горячие клавиши, макросы",
         "https://www.autohotkey.com"),
        ("PowerAutomate Desktop",    "Автоматизация рутинных задач от Microsoft (встроен в Windows 11)",
         "https://www.microsoft.com/ru-ru/power-platform/products/power-automate"),
        ("Keypirinha",               "Быстрый лаунчер и командная строка для Windows",
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

        btn_back = QPushButton("← Назад")
        btn_back.setProperty("cssClass", "flat")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(on_back)
        header_lo.addWidget(btn_back)

        title_lbl = QLabel("💡 Рекомендации при чистой установке Windows")
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

        hint = QLabel(
            "Список полезных программ, которые стоит установить после чистой инсталляции Windows. "
            "Нажмите на ссылку рядом с названием, чтобы открыть официальную страницу."
        )
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "muted")
        content_lo.addWidget(hint)

        for category, items in RECOMMENDATIONS:
            content_lo.addWidget(self._build_section(category, items))

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

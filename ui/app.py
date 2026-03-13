"""Главное окно приложения (PySide6)."""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QStatusBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from utils.i18n import tr, get_language, set_language

logger = logging.getLogger(__name__)


class App(QMainWindow):
    """Главное окно WinRecover."""

    def __init__(self, initial_state: str = "start", config_path: Path | None = None,
                 log_file: Path | None = None):
        super().__init__()
        logger.info("[App] Инициализация, state=%s, config=%s", initial_state, config_path)

        self._config_path = config_path
        self._log_file = log_file
        self._log_window = None
        self._current_screen: str = "start"

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._build_statusbar()
        self._apply_title()
        self._apply_icon()

        if initial_state == "restore" and config_path:
            logger.info("[App] Открываю экран восстановления")
            self._show_restore(config_path)
        else:
            logger.info("[App] Открываю стартовый экран")
            self._show_start()

    def _apply_icon(self):
        if getattr(sys, "frozen", False):
            base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        else:
            base = Path(__file__).parent.parent
        icon_path = base / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _apply_title(self):
        self.setWindowTitle(tr("app.window_title"))
        self.setMinimumSize(900, 650)
        self.resize(950, 700)

    def _build_statusbar(self):
        bar = QStatusBar()
        bar.setStyleSheet("QStatusBar { border-top: 1px solid #313244; background: #1e1e2e; }")
        self.setStatusBar(bar)

        self._btn_lang = QPushButton(tr("app.btn_lang"))
        self._btn_lang.setProperty("cssClass", "flat")
        self._btn_lang.setFixedHeight(24)
        self._btn_lang.setCursor(Qt.PointingHandCursor)
        self._btn_lang.setToolTip("Switch language / Сменить язык")
        self._btn_lang.clicked.connect(self._toggle_language)
        bar.addPermanentWidget(self._btn_lang)

        btn_logs = QPushButton(tr("app.btn_logs"))
        btn_logs.setProperty("cssClass", "flat")
        btn_logs.setFixedHeight(24)
        btn_logs.setCursor(Qt.PointingHandCursor)
        btn_logs.clicked.connect(self._show_log_window)
        bar.addPermanentWidget(btn_logs)

    def _toggle_language(self):
        new_lang = "en" if get_language() == "ru" else "ru"
        set_language(new_lang)
        self._btn_lang.setText(tr("app.btn_lang"))
        self._apply_title()
        self._rebuild_current()

    def _rebuild_current(self):
        """Перестраивает текущий экран после смены языка."""
        screen = self._current_screen
        if screen == "start":
            self._show_start()
        elif screen == "prepare":
            self._show_prepare()
        elif screen == "restore":
            self._show_restore(self._config_path)
        elif screen == "recommendations":
            self._show_recommendations()

    def _show_log_window(self):
        from ui.log_window import LogWindow
        if self._log_window is None or not self._log_window.isVisible():
            self._log_window = LogWindow(log_file=self._log_file, parent=self)
        self._log_window.show()
        self._log_window.raise_()
        self._log_window.activateWindow()

    def _clear_stack(self):
        while self._stack.count() > 0:
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()

    def _show_start(self):
        logger.info("[App] -> Стартовый экран")
        self._current_screen = "start"
        self._clear_stack()
        from ui.start_screen import StartScreen
        screen = StartScreen(
            on_prepare=self._show_prepare,
            on_restore=lambda: self._show_restore(self._config_path),
            on_recommendations=self._show_recommendations,
        )
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_prepare(self):
        logger.info("[App] -> Экран подготовки")
        self._current_screen = "prepare"
        self._clear_stack()
        from ui.prepare_screen import PrepareScreen
        screen = PrepareScreen(on_back=self._show_start)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_recommendations(self):
        logger.info("[App] -> Экран рекомендаций")
        self._current_screen = "recommendations"
        self._clear_stack()
        from ui.recommendations_screen import RecommendationsScreen
        screen = RecommendationsScreen(on_back=self._show_start)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_restore(self, config_path: Path | None = None):
        logger.info("[App] -> Экран восстановления, config=%s", config_path)
        self._current_screen = "restore"
        self._clear_stack()
        from ui.restore_screen import RestoreScreen
        screen = RestoreScreen(on_back=self._show_start, config_path=config_path)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

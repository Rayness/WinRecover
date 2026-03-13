"""Главное окно приложения (PySide6)."""

import logging
from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QStatusBar

from ui.start_screen import StartScreen
from ui.prepare_screen import PrepareScreen
from ui.restore_screen import RestoreScreen
from ui.recommendations_screen import RecommendationsScreen

logger = logging.getLogger(__name__)


class App(QMainWindow):
    """Главное окно WinRecover."""

    def __init__(self, initial_state: str = "start", config_path: Path | None = None,
                 log_file: Path | None = None):
        super().__init__()
        logger.info("[App] Инициализация, state=%s, config=%s", initial_state, config_path)

        self.setWindowTitle("WinRecover — Помощник при переустановке Windows")
        self.setMinimumSize(900, 650)
        self.resize(950, 700)

        self._config_path = config_path
        self._log_file = log_file
        self._log_window = None

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._build_statusbar()

        if initial_state == "restore" and config_path:
            logger.info("[App] Открываю экран восстановления")
            self._show_restore(config_path)
        else:
            logger.info("[App] Открываю стартовый экран")
            self._show_start()

    def _build_statusbar(self):
        bar = QStatusBar()
        bar.setStyleSheet("QStatusBar { border-top: 1px solid #313244; background: #1e1e2e; }")
        self.setStatusBar(bar)

        btn_logs = QPushButton("📋 Логи")
        btn_logs.setProperty("cssClass", "flat")
        btn_logs.setFixedHeight(24)
        btn_logs.setCursor(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.PointingHandCursor)
        btn_logs.clicked.connect(self._show_log_window)
        bar.addPermanentWidget(btn_logs)

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
        self._clear_stack()
        screen = StartScreen(
            on_prepare=self._show_prepare,
            on_restore=lambda: self._show_restore(self._config_path),
            on_recommendations=self._show_recommendations,
        )
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_prepare(self):
        logger.info("[App] -> Экран подготовки")
        self._clear_stack()
        screen = PrepareScreen(on_back=self._show_start)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_recommendations(self):
        logger.info("[App] -> Экран рекомендаций")
        self._clear_stack()
        screen = RecommendationsScreen(on_back=self._show_start)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

    def _show_restore(self, config_path: Path | None = None):
        logger.info("[App] -> Экран восстановления, config=%s", config_path)
        self._clear_stack()
        screen = RestoreScreen(on_back=self._show_start, config_path=config_path)
        self._stack.addWidget(screen)
        self._stack.setCurrentWidget(screen)

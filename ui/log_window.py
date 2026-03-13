"""Окно просмотра логов приложения в реальном времени."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QLabel, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor

from utils.i18n import tr

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG":    "#6c7086",
    "INFO":     "#cdd6f4",
    "WARNING":  "#f9e2af",
    "ERROR":    "#f38ba8",
    "CRITICAL": "#ff0000",
}


class LogWindow(QDialog):
    """Плавающее окно с live-логами приложения."""

    def __init__(self, log_file: Path, parent=None):
        super().__init__(parent)
        self._log_file = log_file
        self._auto_scroll = True
        self.setWindowTitle(tr("log.title"))
        self.setMinimumSize(800, 480)
        self.resize(900, 540)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self._build()
        self._load_existing()
        self._connect_handler()

    def _build(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(8, 8, 8, 8)
        lo.setSpacing(6)

        bar = QHBoxLayout()

        self._lbl_status = QLabel(tr("log.waiting"))
        self._lbl_status.setProperty("cssClass", "muted")
        bar.addWidget(self._lbl_status, 1)

        self._chk_scroll = QCheckBox(tr("log.autoscroll"))
        self._chk_scroll.setChecked(True)
        self._chk_scroll.toggled.connect(lambda v: setattr(self, "_auto_scroll", v))
        bar.addWidget(self._chk_scroll)

        btn_clear = QPushButton(tr("log.clear"))
        btn_clear.setProperty("cssClass", "flat")
        btn_clear.clicked.connect(self._clear)
        bar.addWidget(btn_clear)

        btn_close = QPushButton(tr("log.close"))
        btn_close.setProperty("cssClass", "flat")
        btn_close.clicked.connect(self.close)
        bar.addWidget(btn_close)

        lo.addLayout(bar)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(5000)
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.Monospace)
        self._text.setFont(font)
        self._text.setStyleSheet("background: #11111b; color: #cdd6f4; border: 1px solid #313244;")
        lo.addWidget(self._text, 1)

        self._record_count = 0

    def _load_existing(self):
        if not self._log_file or not self._log_file.exists():
            return
        try:
            text = self._log_file.read_text(encoding="utf-8", errors="replace")
            self._text.setPlainText(text)
            self._record_count = text.count("\n")
            self._scroll_to_bottom()
            self._lbl_status.setText(tr("log.loaded", count=self._record_count))
        except OSError:
            pass

    def _connect_handler(self):
        from utils.helpers import get_qt_log_handler
        handler = get_qt_log_handler()
        if handler:
            handler.record_emitted.connect(self._on_record)

    def _on_record(self, level: str, text: str):
        self._record_count += 1
        color = _LEVEL_COLORS.get(level, "#cdd6f4")

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text + "\n", fmt)

        self._lbl_status.setText(tr("log.records", count=self._record_count))
        if self._auto_scroll:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear(self):
        self._text.clear()
        self._record_count = 0
        self._lbl_status.setText(tr("log.cleared"))

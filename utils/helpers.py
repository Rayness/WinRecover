"""Вспомогательные функции."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Qt log handler ────────────────────────────────────────────────────────────

_qt_log_handler: "QtLogHandler | None" = None


def get_qt_log_handler() -> "QtLogHandler | None":
    return _qt_log_handler


class QtLogHandler(logging.Handler):
    """
    Logging handler, который пересылает записи в Qt через сигнал.
    Безопасен из любого потока — сигнал Qt сам управляет очередью.
    """
    def __init__(self):
        super().__init__()
        from PySide6.QtCore import QObject, Signal

        class _Emitter(QObject):
            record_emitted = Signal(str, str)  # (levelname, formatted_text)

        self._emitter = _Emitter()
        self.record_emitted = self._emitter.record_emitted
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord):
        try:
            self._emitter.record_emitted.emit(record.levelname, self.format(record))
        except Exception:
            pass


def format_size(size_bytes: int) -> str:
    """Форматирует размер в байтах в читаемый вид."""
    if size_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_username() -> str:
    """Возвращает имя текущего пользователя."""
    import os
    return os.environ.get("USERNAME") or Path.home().name


def setup_logging(log_file: Path | None = None):
    """Настраивает логирование. Возвращает путь к лог-файлу."""
    global _qt_log_handler
    if log_file is None:
        log_file = Path(__file__).parent.parent / "app.log"

    qt_handler = QtLogHandler()
    _qt_log_handler = qt_handler

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
            qt_handler,
        ],
    )
    return log_file

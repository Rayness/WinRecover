"""Модальное окно прогресса на PySide6."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PySide6.QtCore import Qt, Signal, Slot

from utils.helpers import format_size


class ProgressModal(QDialog):
    """Модальное окно с прогресс-баром для длительных операций."""

    # Сигнал для безопасного обновления из потока
    progress_updated = Signal(str, float, float, float)

    def __init__(self, parent, title: str = "Выполняется..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(520, 200)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        self._cancelled = False
        self._build_ui()
        self.progress_updated.connect(self._do_update)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 16)

        # Текущий файл
        self.lbl_file = QLabel("Подготовка...")
        self.lbl_file.setWordWrap(True)
        layout.addWidget(self.lbl_file)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Скорость и время
        info_layout = QHBoxLayout()
        self.lbl_speed = QLabel("Скорость: —")
        self.lbl_speed.setProperty("cssClass", "muted")
        self.lbl_eta = QLabel("Осталось: —")
        self.lbl_eta.setProperty("cssClass", "muted")
        self.lbl_eta.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.lbl_speed)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_eta)
        layout.addLayout(info_layout)

        layout.addStretch()

        # Кнопка отмены
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setProperty("cssClass", "danger")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _on_cancel(self):
        self._cancelled = True
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Отмена...")

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def update_progress(self, current_file: str, percent: float, speed_bps: float, eta_seconds: float):
        """Потокобезопасное обновление — вызывает сигнал."""
        self.progress_updated.emit(current_file, percent, speed_bps, eta_seconds)

    @Slot(str, float, float, float)
    def _do_update(self, current_file: str, percent: float, speed_bps: float, eta_seconds: float):
        short = current_file
        if len(short) > 65:
            short = "..." + short[-62:]
        self.lbl_file.setText(short)
        self.progress_bar.setValue(int(percent * 10))
        self.progress_bar.setFormat(f"{percent:.1f}%")
        self.lbl_speed.setText(f"Скорость: {format_size(int(speed_bps))}/с")

        if eta_seconds > 0:
            mins, secs = divmod(int(eta_seconds), 60)
            if mins > 0:
                self.lbl_eta.setText(f"Осталось: {mins} мин {secs} сек")
            else:
                self.lbl_eta.setText(f"Осталось: {secs} сек")
        else:
            self.lbl_eta.setText("Осталось: —")

    def allow_close(self):
        """Разрешает закрытие."""
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)

    def closeEvent(self, event):
        if not self._cancelled:
            event.ignore()
        else:
            super().closeEvent(event)

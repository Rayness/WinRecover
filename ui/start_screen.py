"""Стартовый экран — выбор режима (PySide6)."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

from utils.i18n import tr


class StartScreen(QWidget):
    """Экран приветствия с выбором: подготовка или восстановление."""

    def __init__(self, on_prepare: callable, on_restore: callable,
                 on_recommendations: callable, parent=None):
        super().__init__(parent)
        self._build(on_prepare, on_restore, on_recommendations)

    def _build(self, on_prepare, on_restore, on_recommendations):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        # Иконка
        icon_lbl = QLabel("\U0001f527")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 52px;")
        layout.addWidget(icon_lbl)

        # Заголовок
        title = QLabel("WinRecover")
        title.setProperty("cssClass", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Подзаголовок
        subtitle = QLabel(tr("start.subtitle"))
        subtitle.setProperty("cssClass", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        # Карточка: Подготовка
        btn_prepare = QPushButton(
            f"{tr('start.btn_prepare.title')}\n\n{tr('start.btn_prepare.desc')}"
        )
        btn_prepare.setProperty("cssClass", "card")
        btn_prepare.setFixedSize(500, 110)
        btn_prepare.setCursor(Qt.PointingHandCursor)
        btn_prepare.clicked.connect(on_prepare)
        layout.addWidget(btn_prepare, alignment=Qt.AlignCenter)

        layout.addSpacing(10)

        # Карточка: Восстановление
        btn_restore = QPushButton(
            f"{tr('start.btn_restore.title')}\n\n{tr('start.btn_restore.desc')}"
        )
        btn_restore.setProperty("cssClass", "card")
        btn_restore.setFixedSize(500, 110)
        btn_restore.setCursor(Qt.PointingHandCursor)
        btn_restore.clicked.connect(on_restore)
        layout.addWidget(btn_restore, alignment=Qt.AlignCenter)

        layout.addSpacing(10)

        # Карточка: Рекомендации
        btn_rec = QPushButton(
            f"{tr('start.btn_rec.title')}\n\n{tr('start.btn_rec.desc')}"
        )
        btn_rec.setProperty("cssClass", "card")
        btn_rec.setFixedSize(500, 110)
        btn_rec.setCursor(Qt.PointingHandCursor)
        btn_rec.clicked.connect(on_recommendations)
        layout.addWidget(btn_rec, alignment=Qt.AlignCenter)

        layout.addStretch()

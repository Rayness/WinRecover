"""Тёмная тема и стили приложения."""

from pathlib import Path

_RESOURCES = Path(__file__).parent / "resources"


def _url(name: str) -> str:
    """Возвращает Qt-совместимый URL к файлу ресурса (forward slashes)."""
    return str(_RESOURCES / name).replace("\\", "/")


def get_dark_stylesheet() -> str:
    """Возвращает QSS тёмной темы с правильными путями к ресурсам."""
    return (
        _DARK_STYLESHEET_TEMPLATE
        .replace("{arrow_closed}", _url("arrow_closed.svg"))
        .replace("{arrow_open}", _url("arrow_open.svg"))
    )


# Оставляем DARK_STYLESHEET для обратной совместимости (вычисляется при импорте)
DARK_STYLESHEET = None  # Будет переопределён ниже


_DARK_STYLESHEET_TEMPLATE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ─── Кнопки ─────────────────────────────── */
QPushButton {
    background-color: #2a2a4a;
    color: #e0e0e0;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #3a3a5a;
    border-color: #4a4a6a;
}
QPushButton:pressed {
    background-color: #1a1a3a;
}
QPushButton:disabled {
    background-color: #1a1a2e;
    color: #555;
    border-color: #2a2a3a;
}
QPushButton[cssClass="primary"] {
    background-color: #2563EB;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton[cssClass="primary"]:hover {
    background-color: #1D4ED8;
}
QPushButton[cssClass="success"] {
    background-color: #16A34A;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton[cssClass="success"]:hover {
    background-color: #15803D;
}
QPushButton[cssClass="danger"] {
    background-color: #DC2626;
    color: white;
    border: none;
}
QPushButton[cssClass="danger"]:hover {
    background-color: #B91C1C;
}
QPushButton[cssClass="flat"] {
    background-color: transparent;
    border: none;
    color: #aaa;
}
QPushButton[cssClass="flat"]:hover {
    background-color: #2a2a4a;
    color: #fff;
}

/* ─── Карточки на стартовом экране ──────── */
QPushButton[cssClass="card"] {
    background-color: #16213e;
    border: 2px solid #2a2a4a;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    font-size: 15px;
}
QPushButton[cssClass="card"]:hover {
    border-color: #2563EB;
    background-color: #1a2744;
}

/* ─── Таблицы ────────────────────────────── */
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a2744;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    gridline-color: #2a2a4a;
    selection-background-color: #2563EB;
    selection-color: white;
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background-color: #0f1a30;
    color: #aaa;
    border: none;
    border-right: 1px solid #2a2a4a;
    border-bottom: 1px solid #2a2a4a;
    padding: 6px 8px;
    font-weight: bold;
    font-size: 12px;
}

/* ─── TreeWidget ─────────────────────────── */
QTreeWidget {
    background-color: #16213e;
    alternate-background-color: #1a2744;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    selection-background-color: #2563EB;
    selection-color: white;
    outline: none;
}
QTreeWidget::item {
    padding: 4px 2px;
    border-bottom: 1px solid #1a1a2e;
}
QTreeWidget::item:hover {
    background-color: #1e2d4d;
}
QTreeWidget::item:selected {
    background-color: #2563EB;
}
QTreeWidget::branch {
    background-color: transparent;
}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url("{arrow_closed}");
}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
    image: url("{arrow_open}");
}

/* ─── Вкладки ────────────────────────────── */
QTabWidget::pane {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background-color: #1a1a2e;
    color: #888;
    border: 1px solid #2a2a4a;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #16213e;
    color: #fff;
    border-bottom: 2px solid #2563EB;
}
QTabBar::tab:hover:!selected {
    background-color: #1e2d4d;
    color: #ccc;
}

/* ─── Поля ввода ─────────────────────────── */
QLineEdit, QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #2563EB;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #2563EB;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #888;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    selection-background-color: #2563EB;
}

/* ─── Чекбоксы / Радио ───────────────────── */
QCheckBox, QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3a3a5a;
    border-radius: 3px;
    background-color: #16213e;
}
QRadioButton::indicator {
    border-radius: 10px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

/* ─── Прогресс-бар ───────────────────────── */
QProgressBar {
    background-color: #0f1a30;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    height: 22px;
    font-size: 12px;
}
QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 5px;
}

/* ─── Скроллбар ──────────────────────────── */
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #3a3a5a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4a4a6a;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
QScrollBar:horizontal {
    height: 10px;
}
QScrollBar::handle:horizontal {
    background-color: #3a3a5a;
    border-radius: 5px;
}

/* ─── Лейблы ─────────────────────────────── */
QLabel {
    color: #e0e0e0;
}
QLabel[cssClass="title"] {
    font-size: 28px;
    font-weight: bold;
}
QLabel[cssClass="subtitle"] {
    font-size: 14px;
    color: #888;
}
QLabel[cssClass="heading"] {
    font-size: 14px;
    font-weight: bold;
}
QLabel[cssClass="muted"] {
    color: #666;
    font-size: 12px;
}
QLabel[cssClass="warning"] {
    background-color: #92400E;
    color: white;
    border-radius: 6px;
    padding: 8px 12px;
}
QLabel[cssClass="error"] {
    background-color: #7F1D1D;
    color: white;
    border-radius: 6px;
    padding: 8px 12px;
}
QLabel[cssClass="badge-config"] {
    background-color: #1E3A5F;
    color: #60A5FA;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
}
QLabel[cssClass="badge-other"] {
    background-color: #3B3B1F;
    color: #FACC15;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
}

/* ─── Фреймы / Группы ────────────────────── */
QFrame[cssClass="panel"] {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
}
QGroupBox {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ─── Диалоги ────────────────────────────── */
QDialog {
    background-color: #1a1a2e;
}
QMessageBox {
    background-color: #1a1a2e;
}
QMessageBox QLabel {
    color: #e0e0e0;
}
"""

# Вычисляется при импорте для обратной совместимости
DARK_STYLESHEET = get_dark_stylesheet()

"""Компонент таблицы дисков на PySide6."""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

from core.disk_analyzer import DiskPartition
from utils.helpers import format_size


class DiskTable(QTableWidget):
    """Таблица разделов дисков."""

    def __init__(self, partitions: list[DiskPartition], parent=None):
        super().__init__(len(partitions), 5, parent)
        self.setHorizontalHeaderLabels(["Диск", "Метка", "Всего", "Свободно", "Использ."])
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setMaximumHeight(min(36 * len(partitions) + 34, 250))

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        for row, part in enumerate(partitions):
            self._set_cell(row, 0, part.mountpoint.rstrip("\\"))
            self._set_cell(row, 1, part.label or "—")
            self._set_cell(row, 2, format_size(part.total), Qt.AlignRight)
            self._set_cell(row, 3, format_size(part.free), Qt.AlignRight)
            self._set_cell(row, 4, f"{part.usage_percent:.0f}%", Qt.AlignCenter)

    def _set_cell(self, row: int, col: int, text: str, alignment=Qt.AlignLeft):
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment | Qt.AlignVCenter)
        self.setItem(row, col, item)

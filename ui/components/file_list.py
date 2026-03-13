"""Компонент списка файлов: QTreeWidget с чекбоксами и раскрытием."""

import subprocess
from collections import defaultdict
from pathlib import Path

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from utils.helpers import format_size

SORT_ROLE = Qt.UserRole + 1
PRIORITY_ROLE = Qt.UserRole + 2

_COLOR_IMPORTANT = QColor("#4caf50")
_COLOR_SKIP = QColor("#555577")

# Категории типов файлов для группировки
_EXT_TO_TYPE: dict[str, str] = {}
_TYPE_DEFS = [
    ("📄 Документы",   ["doc", "docx", "odt", "rtf", "txt", "pdf"]),
    ("📊 Таблицы",     ["xls", "xlsx", "csv", "ods"]),
    ("📊 Презентации", ["ppt", "pptx", "odp"]),
    ("🖼 Изображения", ["jpg", "jpeg", "png", "gif", "bmp", "raw", "webp", "tiff", "svg", "ico"]),
    ("🎬 Видео",       ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v"]),
    ("🎵 Аудио",       ["mp3", "flac", "wav", "aac", "ogg", "m4a", "wma"]),
    ("📦 Архивы",      ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"]),
]
for _cat, _exts in _TYPE_DEFS:
    for _e in _exts:
        _EXT_TO_TYPE[_e] = _cat


def _get_type_category(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_TO_TYPE.get(ext, "📎 Прочее")


class _SortableItem(QTreeWidgetItem):
    """QTreeWidgetItem с правильной сортировкой по числовому размеру."""

    def __lt__(self, other):
        tree = self.treeWidget()
        if tree is None:
            return super().__lt__(other)
        col = tree.sortColumn()
        my_val = self.data(col, SORT_ROLE)
        other_val = other.data(col, SORT_ROLE)
        if my_val is not None and other_val is not None:
            return my_val < other_val
        return super().__lt__(other)


_ICONS = {
    "json": "\u2699\ufe0f", "ini": "\u2699\ufe0f", "cfg": "\u2699\ufe0f",
    "conf": "\u2699\ufe0f", "config": "\u2699\ufe0f", "xml": "\u2699\ufe0f",
    "yaml": "\u2699\ufe0f", "yml": "\u2699\ufe0f", "toml": "\u2699\ufe0f",
    "reg": "\u2699\ufe0f", "prefs": "\u2699\ufe0f",
    "db": "\U0001f5c3\ufe0f", "sqlite": "\U0001f5c3\ufe0f",
    "sqlite3": "\U0001f5c3\ufe0f", "ldb": "\U0001f5c3\ufe0f",
    "log": "\U0001f4cb", "txt": "\U0001f4dd",
    "dll": "\U0001f527", "exe": "\U0001f527", "sys": "\U0001f527",
    "doc": "\U0001f4c4", "docx": "\U0001f4c4", "pdf": "\U0001f4d5",
    "xls": "\U0001f4ca", "xlsx": "\U0001f4ca", "ppt": "\U0001f4ca", "pptx": "\U0001f4ca",
    "jpg": "\U0001f5bc\ufe0f", "jpeg": "\U0001f5bc\ufe0f", "png": "\U0001f5bc\ufe0f",
    "gif": "\U0001f5bc\ufe0f", "bmp": "\U0001f5bc\ufe0f", "raw": "\U0001f5bc\ufe0f",
    "mp4": "\U0001f3ac", "avi": "\U0001f3ac", "mov": "\U0001f3ac", "mkv": "\U0001f3ac",
    "mp3": "\U0001f3b5", "flac": "\U0001f3b5", "wav": "\U0001f3b5",
    "zip": "\U0001f4e6", "rar": "\U0001f4e6", "7z": "\U0001f4e6",
}


def _file_icon(name: str, is_dir: bool) -> str:
    if is_dir:
        return "\U0001f4c1"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return _ICONS.get(ext, "\U0001f4c4")


def _open_in_explorer(path: str):
    """Открыть папку или выделить файл в Проводнике."""
    p = Path(path)
    try:
        if p.is_dir():
            subprocess.Popen(["explorer", str(p)])
        elif p.is_file():
            subprocess.Popen(["explorer", "/select,", str(p)])
        else:
            # Путь не существует — открываем родительскую папку если есть
            if p.parent.exists():
                subprocess.Popen(["explorer", str(p.parent)])
    except Exception:
        pass


class FileTreeWidget(QTreeWidget):
    """
    Дерево файлов с чекбоксами.
    config: [Имя, Тип, Расположение, Размер]
    personal: [Имя, Папка, Размер]
    """

    selection_changed = Signal()

    def __init__(self, item_type: str = "config", show_remove: bool = False, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.show_remove = show_remove
        self._propagating = False
        self._last_clicked: QTreeWidgetItem | None = None

        if item_type == "config":
            self.setHeaderLabels(["Имя", "Тип", "Расположение", "Размер"])
            self.setColumnCount(4)
        else:
            self.setHeaderLabels(["Имя", "Папка", "Размер"])
            self.setColumnCount(3)

        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setAnimated(True)
        self.setUniformRowHeights(False)
        self.setSortingEnabled(True)

        header = self.header()
        # Все колонки — интерактивный ресайз (как в Windows Explorer)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setSortIndicatorShown(True)
        header.setMinimumSectionSize(60)

        # Начальные ширины колонок
        if item_type == "config":
            self.setColumnWidth(0, 260)
            self.setColumnWidth(1, 80)
            self.setColumnWidth(2, 90)
            self.setColumnWidth(3, 90)
        else:
            self.setColumnWidth(0, 280)
            self.setColumnWidth(1, 220)
            self.setColumnWidth(2, 90)

        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_double_click)

    def _on_double_click(self, item: QTreeWidgetItem, _column: int):
        """Двойной клик — открыть папку/файл в Проводнике."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        path = data.get("source_path", "")
        if path:
            _open_in_explorer(path)

    def mousePressEvent(self, event):
        """Shift+click — выделить диапазон элементов."""
        from PySide6.QtCore import Qt as _Qt
        item = self.itemAt(event.pos())

        if (item
                and item.flags() & _Qt.ItemIsUserCheckable
                and event.modifiers() & _Qt.ShiftModifier
                and self._last_clicked is not None):
            all_items = self._get_checkable_items_flat()
            try:
                idx1 = all_items.index(self._last_clicked)
                idx2 = all_items.index(item)
            except ValueError:
                super().mousePressEvent(event)
                return
            # Новое состояние — противоположное текущему у кликнутого элемента
            new_state = _Qt.Unchecked if item.checkState(0) == _Qt.Checked else _Qt.Checked
            start, end = min(idx1, idx2), max(idx1, idx2)
            for i in range(start, end + 1):
                all_items[i].setCheckState(0, new_state)
            self._last_clicked = item
            return  # Не передаём дальше — диапазон уже выставлен

        # Обычный клик: запоминаем элемент
        if item and item.flags() & _Qt.ItemIsUserCheckable:
            if not (event.modifiers() & _Qt.ShiftModifier):
                self._last_clicked = item
        super().mousePressEvent(event)

    def _get_checkable_items_flat(self) -> list[QTreeWidgetItem]:
        """Все чекабельные элементы дерева в порядке обхода (DFS), включая свёрнутые."""
        result = []

        def _walk(item: QTreeWidgetItem):
            if item.flags() & Qt.ItemIsUserCheckable:
                result.append(item)
            for i in range(item.childCount()):
                _walk(item.child(i))

        for i in range(self.topLevelItemCount()):
            _walk(self.topLevelItem(i))
        return result

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        if column != 0 or self._propagating:
            return
        self._propagating = True
        try:
            # Элемент с дочерними → рекурсивно распространить состояние вниз
            if item.childCount() > 0:
                state = item.checkState(0)
                if state != Qt.PartiallyChecked:
                    self._propagate_down(item, state)

            # Обновить tri-state всех предков снизу вверх
            self._update_ancestors(item)
        finally:
            self._propagating = False
        self.selection_changed.emit()

    def _propagate_down(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """Рекурсивно устанавливает состояние чекбокса для всех потомков."""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.flags() & Qt.ItemIsUserCheckable:
                child.setCheckState(0, state)
            if child.childCount() > 0:
                self._propagate_down(child, state)

    def _update_ancestors(self, item: QTreeWidgetItem):
        """Обновляет tri-state родителей снизу вверх."""
        parent = item.parent()
        while parent is not None:
            checkable = [
                parent.child(i) for i in range(parent.childCount())
                if parent.child(i).flags() & Qt.ItemIsUserCheckable
            ]
            if checkable:
                checked = sum(1 for c in checkable if c.checkState(0) == Qt.Checked)
                partial = sum(1 for c in checkable if c.checkState(0) == Qt.PartiallyChecked)
                if checked == 0 and partial == 0:
                    parent.setCheckState(0, Qt.Unchecked)
                elif checked == len(checkable):
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)
            parent = parent.parent()

    # ─── Добавление элементов ─────────────────────────────────────────────

    def add_item(self, name: str, path: str, size: int, is_dir: bool,
                 data: dict | None = None, content_type: str = "",
                 children: list | None = None,
                 location: str = "",
                 priority: str = "",
                 priority_reason: str = "") -> QTreeWidgetItem:
        """Добавляет элемент верхнего уровня."""
        icon = _file_icon(name, is_dir)

        if priority == "important":
            display_name = f"⭐  {icon}  {name}"
        elif priority == "skip":
            display_name = f"💤  {icon}  {name}"
        else:
            display_name = f"{icon}  {name}"

        item = _SortableItem()
        item.setText(0, display_name)
        item.setCheckState(0, Qt.Unchecked)
        item.setData(0, Qt.UserRole, data or {})
        item.setData(0, SORT_ROLE, name.lower())
        item.setData(0, PRIORITY_ROLE, priority)

        if priority_reason:
            tip = (
                f"{'✅ Рекомендуем сохранить' if priority == 'important' else '⏭ Можно пропустить'}"
                f": {priority_reason}\n"
                f"Двойной клик — открыть папку"
            )
            item.setToolTip(0, tip)
        else:
            item.setToolTip(0, "Двойной клик — открыть папку")

        if priority == "skip":
            for col in range(self.columnCount()):
                item.setForeground(col, _COLOR_SKIP)

        if self.item_type == "config":
            if content_type:
                badge = "Конфиг" if content_type == "config" else "Другое"
                item.setText(1, badge)
                item.setData(1, SORT_ROLE, badge)
            if location:
                item.setText(2, location)
                item.setData(2, SORT_ROLE, location)
            size_col = 3
        else:
            # Личные: col 1 = родительская папка (не полный путь)
            parent_folder = str(Path(path).parent.name) if path else ""
            item.setText(1, parent_folder)
            item.setData(1, SORT_ROLE, parent_folder.lower())
            size_col = 2

        item.setText(size_col, format_size(size))
        item.setData(size_col, SORT_ROLE, size)
        item.setTextAlignment(size_col, Qt.AlignRight | Qt.AlignVCenter)

        self.addTopLevelItem(item)

        # Дочерние элементы для раскрытия (config-папки)
        if children and is_dir and self.item_type == "config":
            shown = children[:80]
            for child in shown:
                child_icon = _file_icon(child.name, child.is_dir)
                child_item = QTreeWidgetItem()
                child_item.setText(0, f"    {child_icon}  {child.name}")
                child_item.setFlags(child_item.flags() & ~Qt.ItemIsUserCheckable)
                child_item.setText(3, format_size(child.size) if child.size > 0 else "")
                child_item.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
                child_item.setForeground(0, Qt.gray)
                child_item.setForeground(3, Qt.darkGray)
                item.addChild(child_item)
            if len(children) > 80:
                more = QTreeWidgetItem()
                more.setText(0, f"    ... и ещё {len(children) - 80} элементов")
                more.setForeground(0, Qt.darkGray)
                more.setFlags(more.flags() & ~Qt.ItemIsUserCheckable)
                item.addChild(more)

        return item

    def add_grouped_items(self, items: list[dict], group_by: str = "folder"):
        """
        Добавляет личные файлы с группировкой.
        group_by: "folder" | "type" | "folder+type"
        """
        if group_by == "folder":
            self._add_grouped_by_folder(items)
        elif group_by == "type":
            self._add_grouped_by_type(items)
        elif group_by == "folder+type":
            self._add_grouped_by_folder_and_type(items)

    def _make_group_header(self, label: str, count: int, total_size: int) -> "_SortableItem":
        item = _SortableItem()
        item.setText(0, label)
        item.setCheckState(0, Qt.Unchecked)
        item.setData(0, Qt.UserRole, None)
        item.setData(0, SORT_ROLE, label.lower())
        item.setText(1, f"{count} файлов")
        item.setData(1, SORT_ROLE, label.lower())
        item.setText(2, format_size(total_size))
        item.setData(2, SORT_ROLE, total_size)
        item.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
        return item

    def _make_file_child(self, e: dict, show_subfolder: bool = True) -> "_SortableItem":
        size = e.get("size_bytes", 0)
        name = e.get("name", Path(e.get("source_path", "unknown")).name)
        icon = _file_icon(name, e.get("is_dir", False))
        child = _SortableItem()
        child.setText(0, f"    {icon}  {name}")
        child.setCheckState(0, Qt.Unchecked)
        child.setData(0, Qt.UserRole, e)
        child.setData(0, SORT_ROLE, name.lower())
        child.setToolTip(0, "Двойной клик — открыть в Проводнике")
        if show_subfolder:
            rel = e.get("relative_path", "")
            parts = Path(rel).parts
            subfolder = str(Path(*parts[1:-1])) if len(parts) > 2 else ""
            child.setText(1, subfolder)
            child.setData(1, SORT_ROLE, subfolder.lower())
        child.setText(2, format_size(size))
        child.setData(2, SORT_ROLE, size)
        child.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
        return child

    def _add_grouped_by_folder(self, items: list[dict]):
        groups: dict[str, list[dict]] = defaultdict(list)
        for e in items:
            parts = Path(e.get("relative_path", "")).parts
            groups[parts[0] if parts else "Прочее"].append(e)
        for cat in sorted(groups.keys()):
            entries = groups[cat]
            total = sum(e.get("size_bytes", 0) for e in entries)
            header = self._make_group_header(f"\U0001f4c1  {cat}", len(entries), total)
            self.addTopLevelItem(header)
            for e in sorted(entries, key=lambda x: x.get("name", "").lower()):
                header.addChild(self._make_file_child(e, show_subfolder=True))

    def _add_grouped_by_type(self, items: list[dict]):
        groups: dict[str, list[dict]] = defaultdict(list)
        for e in items:
            groups[_get_type_category(e.get("name", ""))].append(e)
        for cat in sorted(groups.keys()):
            entries = groups[cat]
            total = sum(e.get("size_bytes", 0) for e in entries)
            header = self._make_group_header(cat, len(entries), total)
            self.addTopLevelItem(header)
            for e in sorted(entries, key=lambda x: x.get("name", "").lower()):
                child = self._make_file_child(e, show_subfolder=False)
                # показать папку в col 1
                rel = e.get("relative_path", "")
                parts = Path(rel).parts
                folder = parts[0] if parts else ""
                child.setText(1, folder)
                child.setData(1, SORT_ROLE, folder.lower())
                header.addChild(child)

    def _add_grouped_by_folder_and_type(self, items: list[dict]):
        """Двойная группировка: папка → тип файлов → файлы."""
        folder_groups: dict[str, list[dict]] = defaultdict(list)
        for e in items:
            parts = Path(e.get("relative_path", "")).parts
            folder_groups[parts[0] if parts else "Прочее"].append(e)

        for folder in sorted(folder_groups.keys()):
            folder_entries = folder_groups[folder]
            folder_total = sum(e.get("size_bytes", 0) for e in folder_entries)
            folder_header = self._make_group_header(
                f"\U0001f4c1  {folder}", len(folder_entries), folder_total
            )
            self.addTopLevelItem(folder_header)

            type_groups: dict[str, list[dict]] = defaultdict(list)
            for e in folder_entries:
                type_groups[_get_type_category(e.get("name", ""))].append(e)

            for type_cat in sorted(type_groups.keys()):
                type_entries = type_groups[type_cat]
                type_total = sum(e.get("size_bytes", 0) for e in type_entries)
                type_header = _SortableItem()
                type_header.setText(0, f"    {type_cat}")
                type_header.setCheckState(0, Qt.Unchecked)
                type_header.setData(0, Qt.UserRole, None)
                type_header.setData(0, SORT_ROLE, type_cat.lower())
                type_header.setText(1, f"{len(type_entries)} файлов")
                type_header.setText(2, format_size(type_total))
                type_header.setData(2, SORT_ROLE, type_total)
                type_header.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
                folder_header.addChild(type_header)

                for e in sorted(type_entries, key=lambda x: x.get("name", "").lower()):
                    child = self._make_file_child(e, show_subfolder=True)
                    # Добавить ещё одно отступление
                    child.setText(0, "    " + child.text(0).lstrip())
                    type_header.addChild(child)

    # ─── Выделение ────────────────────────────────────────────────────────

    def select_all(self):
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setCheckState(0, Qt.Checked)

    def deselect_all(self):
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setCheckState(0, Qt.Unchecked)

    def select_by_type(self, badge: str):
        """Выделить элементы по типу ('Конфиг' или 'Другое'), остальные снять."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.text(1) == badge:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)

    def select_recommended(self):
        """Выделить только рекомендованные (important), снять остальные."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, PRIORITY_ROLE) == "important":
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)

    # ─── Получение данных ─────────────────────────────────────────────────

    def get_selected_data(self) -> list[dict]:
        """Возвращает data всех отмеченных листовых элементов (любой глубины)."""
        result = []
        for i in range(self.topLevelItemCount()):
            self._collect_selected(self.topLevelItem(i), result)
        return result

    def _collect_selected(self, item: QTreeWidgetItem, result: list):
        """Рекурсивно собирает данные отмеченных листовых элементов."""
        checkable_children = [
            item.child(j) for j in range(item.childCount())
            if item.child(j).flags() & Qt.ItemIsUserCheckable
        ]
        if checkable_children:
            # Не листовой — идём глубже
            for child in checkable_children:
                self._collect_selected(child, result)
        else:
            # Листовой элемент — берём если отмечен
            if item.checkState(0) == Qt.Checked:
                data = item.data(0, Qt.UserRole)
                if data:
                    result.append(data)

    def remove_selected(self):
        to_remove = []
        for i in range(self.topLevelItemCount()):
            if self.topLevelItem(i).checkState(0) == Qt.Checked:
                to_remove.append(i)
        for i in reversed(to_remove):
            self.takeTopLevelItem(i)

    def get_all_data(self) -> list[dict]:
        result = []
        for i in range(self.topLevelItemCount()):
            self._collect_all(self.topLevelItem(i), result)
        return result

    def _collect_all(self, item: QTreeWidgetItem, result: list):
        """Рекурсивно собирает данные всех листовых элементов."""
        checkable_children = [
            item.child(j) for j in range(item.childCount())
            if item.child(j).flags() & Qt.ItemIsUserCheckable
        ]
        if checkable_children:
            for child in checkable_children:
                self._collect_all(child, result)
        else:
            data = item.data(0, Qt.UserRole)
            if data:
                result.append(data)

    def get_total_size(self) -> int:
        return sum(d.get("size_bytes", 0) for d in self.get_all_data())

    def get_selected_size(self) -> int:
        return sum(d.get("size_bytes", 0) for d in self.get_selected_data())

    def count_items(self) -> int:
        return self.topLevelItemCount()

    def get_stats(self) -> tuple[int, int, int, int]:
        """Возвращает (выбрано листов, всего листов, выбранный размер, общий размер)."""
        selected = self.get_selected_data()
        total = self.get_all_data()
        sel_size = sum(d.get("size_bytes", 0) for d in selected)
        tot_size = sum(d.get("size_bytes", 0) for d in total)
        return len(selected), len(total), sel_size, tot_size

    # ─── Фильтрация ───────────────────────────────────────────────────────

    def filter_items(self, text: str):
        """Скрывает элементы, не подходящие под поисковый запрос."""
        text_lower = text.lower().strip()
        for i in range(self.topLevelItemCount()):
            self._filter_item(self.topLevelItem(i), text_lower)

    def _filter_item(self, item: QTreeWidgetItem, text: str) -> bool:
        """Рекурсивно показывает/скрывает элемент. Возвращает True если виден."""
        if not text:
            item.setHidden(False)
            for j in range(item.childCount()):
                self._filter_item(item.child(j), text)
            return True

        name = item.text(0).lower()
        self_matches = text in name

        child_visible = False
        for j in range(item.childCount()):
            if self._filter_item(item.child(j), text):
                child_visible = True

        visible = self_matches or child_visible
        item.setHidden(not visible)
        return visible

    # ─── Контекстное меню ─────────────────────────────────────────────────

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu = QMenu(self)

        if item:
            data = item.data(0, Qt.UserRole)
            if data:
                path = data.get("source_path", "")
                if path:
                    act_open = menu.addAction("📂 Открыть в Проводнике")
                    act_open.triggered.connect(lambda: _open_in_explorer(path))
                    menu.addSeparator()

            if item.flags() & Qt.ItemIsUserCheckable:
                act_check = menu.addAction("✅ Отметить")
                act_check.triggered.connect(lambda: item.setCheckState(0, Qt.Checked))
                act_uncheck = menu.addAction("☐ Снять отметку")
                act_uncheck.triggered.connect(lambda: item.setCheckState(0, Qt.Unchecked))

        if not menu.isEmpty():
            menu.exec(event.globalPos())

    # ─── Горячие клавиши ──────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            self.select_all()
        elif event.key() == Qt.Key_Escape:
            self.deselect_all()
        else:
            super().keyPressEvent(event)

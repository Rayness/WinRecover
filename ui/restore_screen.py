"""Экран восстановления после переустановки (PySide6)."""

import logging
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFileDialog, QMessageBox, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QObject

import config_manager
from core.file_operations import CopyProgress, restore_entries
from ui.components.file_list import FileTreeWidget
from ui.components.progress_modal import ProgressModal
from utils.helpers import format_size, get_username
from utils.i18n import tr


def _parse_programs_md(text: str) -> list[tuple[str, list[dict]]]:
    """
    Парсит programs_list.md и возвращает [(категория, [{'name','publisher','version','date'}])].
    """
    categories: list[tuple[str, list[dict]]] = []
    current_cat: str | None = None
    current_entries: list[dict] = []
    header_done = False

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if current_cat is not None:
                categories.append((current_cat, current_entries))
            current_cat = line[3:].strip()
            current_entries = []
            header_done = False
        elif line.startswith("|") and current_cat:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if not cols:
                continue
            # Разделитель |---|---|...
            if all(c.lstrip("-:").strip() == "" for c in cols if c):
                header_done = True
                continue
            if not header_done:
                # Заголовок таблицы — пропускаем
                continue
            name = cols[0].replace("\\|", "|") if cols else ""
            pub = cols[1].replace("\\|", "|") if len(cols) > 1 else ""
            ver = cols[2] if len(cols) > 2 else ""
            date = cols[3] if len(cols) > 3 else ""
            if name and name != "—":
                current_entries.append({
                    "name": name,
                    "publisher": "" if pub == "—" else pub,
                    "version": "" if ver == "—" else ver,
                    "date": "" if date == "—" else date,
                })

    if current_cat is not None:
        categories.append((current_cat, current_entries))
    return categories

logger = logging.getLogger(__name__)


class _RestoreSignals(QObject):
    finished = Signal(list)


class RestoreScreen(QWidget):

    def __init__(self, on_back: callable, config_path: Path | None = None, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.config_path = config_path
        self.config_data: dict | None = None
        self._build()
        if config_path:
            self._load_config(config_path)
        else:
            self._show_no_config()

    def _build(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        header = QHBoxLayout()
        btn_back = QPushButton(tr("restore.btn_back"))
        btn_back.setProperty("cssClass", "flat")
        btn_back.setFixedWidth(90)
        btn_back.clicked.connect(self.on_back)
        header.addWidget(btn_back)
        self.lbl_title = QLabel(tr("restore.title"))
        self.lbl_title.setProperty("cssClass", "heading")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        header.addWidget(self.lbl_title, 1)
        header.addSpacing(90)
        self.main_layout.addLayout(header)

        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout, 1)

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

    def _show_no_config(self):
        self._clear_content()
        c = QWidget()
        lo = QVBoxLayout(c)
        lo.setAlignment(Qt.AlignCenter)
        icon = QLabel("\U0001f4c2")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        lo.addWidget(icon)
        lbl1 = QLabel(tr("restore.no_config"))
        lbl1.setStyleSheet("font-size: 16px; font-weight: bold;")
        lbl1.setAlignment(Qt.AlignCenter)
        lo.addWidget(lbl1)
        lbl2 = QLabel(tr("restore.no_config_hint"))
        lbl2.setStyleSheet("color: #888;")
        lbl2.setAlignment(Qt.AlignCenter)
        lo.addWidget(lbl2)
        btn = QPushButton(tr("restore.btn_pick_config"))
        btn.setProperty("cssClass", "primary")
        btn.setFixedSize(240, 40)
        btn.clicked.connect(self._browse_config)
        lo.addWidget(btn, alignment=Qt.AlignCenter)
        self.content_layout.addWidget(c)

    def _browse_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("restore.dlg_config_title"), "",
            tr("restore.dlg_config_filter"))
        if path:
            self._load_config(Path(path))

    def _load_config(self, config_path: Path):
        try:
            self.config_data = config_manager.load_config(config_path)
            self.config_path = config_path
        except Exception as e:
            QMessageBox.critical(self, tr("restore.error_title"), tr("restore.error_load", error=e))
            return
        self._build_restore_ui()

    def _build_restore_ui(self):
        self._clear_content()
        config = self.config_data
        old_username = config.get("old_username", "?")
        new_username = get_username()
        session_name = config.get("session_name", tr("restore.no_session_name"))
        created = config.get("created_at", "")
        self.lbl_title.setText(tr("restore.title_session", name=session_name))

        info = QLabel(tr("restore.session_info",
                         name=session_name, date=created, old=old_username, new=new_username))
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #16213e; border-radius: 6px; padding: 10px;")
        self.content_layout.addWidget(info)

        entries = config.get("entries", [])
        configs = [e for e in entries if e.get("type") == "config"]
        personal = [e for e in entries if e.get("type") == "personal"]

        tabview = QTabWidget()
        self.content_layout.addWidget(tabview, 1)
        self.restore_config_tree = None
        self.restore_personal_tree = None

        if configs:
            tab = QWidget()
            lo = QVBoxLayout(tab)
            lo.setContentsMargins(4, 4, 4, 4)
            top = QHBoxLayout()
            b1 = QPushButton(tr("restore.btn_all"))
            b2 = QPushButton(tr("restore.btn_none"))
            top.addWidget(b1); top.addWidget(b2); top.addStretch()
            lo.addLayout(top)
            self.restore_config_tree = FileTreeWidget(item_type="config")
            b1.clicked.connect(lambda: self.restore_config_tree.select_all())
            b2.clicked.connect(lambda: self.restore_config_tree.deselect_all())
            lo.addWidget(self.restore_config_tree, 1)
            for e in configs:
                rel = e.get("relative_path", "")
                dest_rel = rel.replace(old_username, new_username)
                dest_path = str(Path.home() / dest_rel)
                self.restore_config_tree.add_item(
                    name=f"{e.get('name', '?')}  \u2192  {dest_path}",
                    path=e.get("source_path", ""), size=e.get("size_bytes", 0),
                    is_dir=e.get("is_dir", True), data=e)
            tabview.addTab(tab, tr("restore.tab_configs", count=len(configs)))

        if personal:
            tab = QWidget()
            lo = QVBoxLayout(tab)
            lo.setContentsMargins(4, 4, 4, 4)
            top = QHBoxLayout()
            b1 = QPushButton(tr("restore.btn_all"))
            b2 = QPushButton(tr("restore.btn_none"))
            top.addWidget(b1); top.addWidget(b2); top.addStretch()
            lo.addLayout(top)
            self.restore_personal_tree = FileTreeWidget(item_type="personal")
            b1.clicked.connect(lambda: self.restore_personal_tree.select_all())
            b2.clicked.connect(lambda: self.restore_personal_tree.deselect_all())
            lo.addWidget(self.restore_personal_tree, 1)
            for e in personal:
                rel = e.get("relative_path", "")
                dest_rel = rel.replace(old_username, new_username)
                dest_path = str(Path.home() / dest_rel)
                self.restore_personal_tree.add_item(
                    name=f"{e.get('name', Path(e.get('source_path','')).name)}  \u2192  {dest_path}",
                    path=e.get("source_path", ""), size=e.get("size_bytes", 0),
                    is_dir=e.get("is_dir", False), data=e)
            tabview.addTab(tab, tr("restore.tab_personal", count=len(personal)))

        # Вкладка программ (если есть programs_list.md)
        self._load_programs_tab(tabview)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton(tr("restore.btn_restore"))
        btn.setProperty("cssClass", "primary")
        btn.setFixedSize(300, 42)
        btn.clicked.connect(self._start_restore)
        btn_row.addWidget(btn)
        self.content_layout.addLayout(btn_row)

    def _load_programs_tab(self, tabview: QTabWidget):
        """Добавляет вкладку с программами если programs_list.md существует."""
        md_path = self.config_path.parent / "programs_list.md"
        if not md_path.exists():
            return

        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            return

        categories = _parse_programs_md(text)
        if not categories:
            return

        total_count = sum(len(entries) for _, entries in categories)

        tab = QWidget()
        lo = QVBoxLayout(tab)
        lo.setContentsMargins(4, 4, 4, 4)

        # Поиск
        search = QLineEdit()
        search.setPlaceholderText(tr("restore.prog_search"))
        search.setClearButtonEnabled(True)
        lo.addWidget(search)

        # Дерево
        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels([tr("restore.prog_col_name"), tr("restore.prog_col_pub"), tr("restore.prog_col_ver"), tr("restore.prog_col_date")])
        tree.setAlternatingRowColors(True)
        tree.setSortingEnabled(True)
        tree.setRootIsDecorated(True)
        hdr = tree.header()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(False)
        tree.setColumnWidth(0, 260)
        tree.setColumnWidth(1, 180)
        tree.setColumnWidth(2, 100)
        tree.setColumnWidth(3, 100)

        for cat_name, entries in categories:
            cat_item = QTreeWidgetItem()
            cat_item.setText(0, cat_name)
            cat_item.setText(1, tr("restore.prog_count", count=len(entries)))
            cat_item.setExpanded(False)
            tree.addTopLevelItem(cat_item)
            for e in entries:
                row = QTreeWidgetItem()
                row.setText(0, "    " + e["name"])
                row.setText(1, e["publisher"])
                row.setText(2, e["version"])
                row.setText(3, e["date"])
                cat_item.addChild(row)

        lo.addWidget(tree, 1)

        # Статус
        lbl = QLabel(tr("restore.prog_total", count=total_count))
        lbl.setProperty("cssClass", "muted")
        lo.addWidget(lbl)

        # Фильтрация
        def _filter(text: str):
            tl = text.lower()
            visible_total = 0
            for i in range(tree.topLevelItemCount()):
                top = tree.topLevelItem(i)
                any_visible = False
                for j in range(top.childCount()):
                    child = top.child(j)
                    match = not tl or tl in child.text(0).lower() or tl in child.text(1).lower()
                    child.setHidden(not match)
                    if match:
                        any_visible = True
                        visible_total += 1
                top.setHidden(not any_visible)
            lbl.setText(
                tr("restore.prog_found", count=visible_total) if tl
                else tr("restore.prog_total", count=total_count)
            )

        search.textChanged.connect(_filter)

        tabview.addTab(tab, tr("restore.tab_programs", count=total_count))

    def _start_restore(self):
        selected = []
        if self.restore_config_tree:
            selected.extend(self.restore_config_tree.get_selected_data())
        if self.restore_personal_tree:
            selected.extend(self.restore_personal_tree.get_selected_data())
        if not selected:
            QMessageBox.warning(self, tr("restore.warn_title"), tr("restore.warn_pick"))
            return

        config = self.config_data
        old_username = config.get("old_username", "")
        new_username = get_username()
        archive_mode = config.get("archive_mode", False)
        source_folder = self.config_path.parent

        modal = ProgressModal(self, title=tr("restore.progress_title"))
        self._restore_signals = _RestoreSignals()

        def _on_done(results):
            modal.allow_close()
            modal.accept()
            for entry in config.get("entries", []):
                for res in results:
                    if entry.get("source_path") == res.get("source_path"):
                        entry["status"] = res["status"]
            try:
                config_manager.save_config(config, source_folder)
            except Exception:
                pass
            ok = [e for e in results if e.get("status") == "ok"]
            err = [e for e in results if e.get("status", "").startswith("error")]
            msg = tr("restore.results_prefix")
            for e in ok:
                msg += tr("restore.result_ok", name=e.get("name", "?"))
            for e in err:
                msg += tr("restore.result_err", name=e.get("name", "?"), status=e.get("status", ""))
            if err:
                QMessageBox.warning(self, tr("restore.done_title"), msg)
            else:
                QMessageBox.information(self, tr("restore.done_title"), msg)

        self._restore_signals.finished.connect(_on_done)

        def _do():
            def pcb(prog: CopyProgress):
                modal.update_progress(prog.current_file, prog.percent, prog.speed_bps, prog.eta_seconds)
            results = restore_entries(
                entries=selected, source_folder=source_folder,
                old_username=old_username, new_username=new_username,
                archive_mode=archive_mode, progress_callback=pcb,
                cancel_check=lambda: modal.cancelled)
            self._restore_signals.finished.emit(results)

        threading.Thread(target=_do, daemon=True).start()
        modal.exec()

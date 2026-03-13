"""Экран подготовки к переустановке (PySide6)."""

import datetime
import logging
import threading
from pathlib import Path

import psutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTabWidget, QFileDialog, QMessageBox,
    QRadioButton, QButtonGroup, QCheckBox, QDialog, QProgressBar, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor

import config_manager
from core.disk_analyzer import (
    DiskPartition, find_best_destination, get_all_partitions, get_system_disk,
)
from core.file_operations import CopyProgress, copy_entries
from core.file_scanner import FoundItem, scan_appdata, scan_personal_files, scan_ssh_keys
from core.games_scanner import (
    GameInfo, VaultInfo,
    scan_games_on_system_drive, scan_obsidian_vaults,
)
from core.programs_scanner import (
    ProgramInfo, scan_installed_programs, programs_to_markdown, CATEGORIES_ORDER,
)
from ui.components.disk_info import DiskTable
from ui.components.file_list import FileTreeWidget
from ui.components.progress_modal import ProgressModal
from utils.helpers import format_size, get_username
from utils.i18n import tr, tr_cat

logger = logging.getLogger(__name__)


class _ScanSignals(QObject):
    progress = Signal(str)
    finished = Signal()


class _CopySignals(QObject):
    finished = Signal(list)


class PrepareScreen(QWidget):
    """Экран подготовки: шаги 1-4."""

    def __init__(self, on_back: callable, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.partitions: list[DiskPartition] = []
        self.system_disk = ""
        self.found_configs: list[FoundItem] = []
        self.found_personal: list[FoundItem] = []
        self.found_programs: list[ProgramInfo] = []
        self.selected_programs: list[ProgramInfo] = []
        self.added_entries: list[dict] = []
        self._cancel_scan = False
        self._scan_personal = False
        self._current_step = 0
        self._step_widgets: list[QWidget] = []

        self._build()
        self._show_step(0)

    def _build(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        # Заголовок
        header = QHBoxLayout()
        self.btn_back = QPushButton(tr("prepare.btn_back"))
        self.btn_back.setProperty("cssClass", "flat")
        self.btn_back.setFixedWidth(90)
        self.btn_back.clicked.connect(self._go_back)
        header.addWidget(self.btn_back)
        self.lbl_step = QLabel(tr("prepare.step1"))
        self.lbl_step.setProperty("cssClass", "heading")
        self.lbl_step.setAlignment(Qt.AlignCenter)
        header.addWidget(self.lbl_step, 1)
        header.addSpacing(90)
        self.main_layout.addLayout(header)

        self.step_container = QVBoxLayout()
        self.main_layout.addLayout(self.step_container, 1)

        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_step4()

    def _go_back(self):
        if self._current_step > 0:
            self._show_step(self._current_step - 1)
        else:
            self.on_back()

    def _show_step(self, step: int):
        logger.info("[PrepareScreen] Переход на шаг %d", step + 1)
        for w in self._step_widgets:
            w.setVisible(False)
        self._step_widgets[step].setVisible(True)
        self._current_step = step
        titles = [
            tr("prepare.step1"),
            tr("prepare.step2"),
            tr("prepare.step3"),
            tr("prepare.step4"),
        ]
        self.lbl_step.setText(titles[step])
        if step == 0:
            self._analyze_disks()

    # ═══ ШАГ 1: Анализ дисков ═══════════════════════════
    def _build_step1(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_sys_disk = QLabel()
        self.lbl_sys_disk.setProperty("cssClass", "heading")
        layout.addWidget(self.lbl_sys_disk)

        self.lbl_warning = QLabel()
        self.lbl_warning.setVisible(False)
        self.lbl_warning.setWordWrap(True)
        layout.addWidget(self.lbl_warning)

        layout.addWidget(QLabel(tr("prepare.partitions")))
        self.disk_table_container = QVBoxLayout()
        layout.addLayout(self.disk_table_container)

        # ── Предупреждение об играх на C: ───────────────────────────────
        self.games_warn_widget = QWidget()
        self.games_warn_widget.setVisible(False)
        gw_lo = QVBoxLayout(self.games_warn_widget)
        gw_lo.setContentsMargins(0, 4, 0, 4)
        gw_lo.setSpacing(4)

        # Заголовок: иконка + сводка + кнопка раскрытия
        gw_header = QHBoxLayout()
        self.lbl_games_warn = QLabel()
        self.lbl_games_warn.setProperty("cssClass", "warning")
        self.lbl_games_warn.setWordWrap(False)
        gw_header.addWidget(self.lbl_games_warn, 1)
        self.btn_games_toggle = QPushButton(tr("prepare.games.show"))
        self.btn_games_toggle.setProperty("cssClass", "flat")
        self.btn_games_toggle.setFixedWidth(150)
        self.btn_games_toggle.clicked.connect(self._toggle_games_list)
        gw_header.addWidget(self.btn_games_toggle)
        gw_lo.addLayout(gw_header)

        # Таблица игр (скрыта по умолчанию)
        self.games_list_widget = QWidget()
        self.games_list_widget.setVisible(False)
        gl_lo = QVBoxLayout(self.games_list_widget)
        gl_lo.setContentsMargins(0, 0, 0, 0)
        gl_lo.setSpacing(4)

        self.games_tree = QTreeWidget()
        self.games_tree.setColumnCount(3)
        self.games_tree.setHeaderLabels([tr("prepare.games.col_name"), tr("prepare.games.col_plat"), "Размер"])
        self.games_tree.setAlternatingRowColors(True)
        self.games_tree.setRootIsDecorated(False)
        self.games_tree.setSortingEnabled(True)
        self.games_tree.setMaximumHeight(180)
        gh = self.games_tree.header()
        gh.setSectionResizeMode(QHeaderView.Interactive)
        gh.setStretchLastSection(False)
        self.games_tree.setColumnWidth(0, 280)
        self.games_tree.setColumnWidth(1, 110)
        self.games_tree.setColumnWidth(2, 90)
        gl_lo.addWidget(self.games_tree)

        lbl_tip = QLabel(tr("prepare.games.tip"))
        lbl_tip.setWordWrap(True)
        lbl_tip.setProperty("cssClass", "muted")
        gl_lo.addWidget(lbl_tip)

        gw_lo.addWidget(self.games_list_widget)
        layout.addWidget(self.games_warn_widget)

        # ── Предупреждение о хранилищах Obsidian ────────────────────────
        self.vaults_warn_widget = QWidget()
        self.vaults_warn_widget.setVisible(False)
        vw_lo = QVBoxLayout(self.vaults_warn_widget)
        vw_lo.setContentsMargins(0, 4, 0, 4)
        vw_lo.setSpacing(4)

        vw_header = QHBoxLayout()
        self.lbl_vaults_warn = QLabel()
        self.lbl_vaults_warn.setProperty("cssClass", "warning")
        self.lbl_vaults_warn.setWordWrap(False)
        vw_header.addWidget(self.lbl_vaults_warn, 1)
        self.btn_vaults_toggle = QPushButton(tr("prepare.vaults.show"))
        self.btn_vaults_toggle.setProperty("cssClass", "flat")
        self.btn_vaults_toggle.setFixedWidth(150)
        self.btn_vaults_toggle.clicked.connect(self._toggle_vaults_list)
        vw_header.addWidget(self.btn_vaults_toggle)
        vw_lo.addLayout(vw_header)

        self.vaults_list_widget = QWidget()
        self.vaults_list_widget.setVisible(False)
        vl_lo = QVBoxLayout(self.vaults_list_widget)
        vl_lo.setContentsMargins(0, 0, 0, 0)
        vl_lo.setSpacing(4)

        self.vaults_tree = QTreeWidget()
        self.vaults_tree.setColumnCount(3)
        self.vaults_tree.setHeaderLabels([tr("prepare.vaults.col_name"), tr("prepare.vaults.col_path"), "Размер"])
        self.vaults_tree.setAlternatingRowColors(True)
        self.vaults_tree.setRootIsDecorated(False)
        self.vaults_tree.setSortingEnabled(True)
        self.vaults_tree.setMaximumHeight(140)
        vh = self.vaults_tree.header()
        vh.setSectionResizeMode(QHeaderView.Interactive)
        vh.setStretchLastSection(False)
        self.vaults_tree.setColumnWidth(0, 160)
        self.vaults_tree.setColumnWidth(1, 300)
        self.vaults_tree.setColumnWidth(2, 90)
        vl_lo.addWidget(self.vaults_tree)

        lbl_vault_tip = QLabel(tr("prepare.vaults.tip"))
        lbl_vault_tip.setWordWrap(True)
        lbl_vault_tip.setProperty("cssClass", "muted")
        vl_lo.addWidget(lbl_vault_tip)

        vw_lo.addWidget(self.vaults_list_widget)
        layout.addWidget(self.vaults_warn_widget)

        # Настройки
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(tr("prepare.dest_disk")))
        self.combo_dest = QComboBox()
        self.combo_dest.setMinimumWidth(80)
        self.combo_dest.currentTextChanged.connect(self._on_dest_changed)
        row1.addWidget(self.combo_dest)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(tr("prepare.dest_folder")))
        self.edit_folder = QLineEdit()
        self.edit_folder.setMinimumWidth(300)
        row2.addWidget(self.edit_folder, 1)
        btn_browse = QPushButton(tr("prepare.btn_browse"))
        btn_browse.clicked.connect(self._browse_folder)
        row2.addWidget(btn_browse)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel(tr("prepare.session_name")))
        self.edit_session = QLineEdit()
        self.edit_session.setMinimumWidth(300)
        row3.addWidget(self.edit_session, 1)
        layout.addLayout(row3)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_next = QPushButton(tr("prepare.btn_next"))
        btn_next.setProperty("cssClass", "primary")
        btn_next.setFixedSize(140, 38)
        btn_next.clicked.connect(lambda: self._show_step(1))
        btn_row.addWidget(btn_next)
        layout.addLayout(btn_row)

        self.step_container.addWidget(widget)
        self._step_widgets.append(widget)

    def _analyze_disks(self):
        self.system_disk = get_system_disk()
        self.partitions = get_all_partitions()
        self.lbl_sys_disk.setText(tr("prepare.system_disk", disk=self.system_disk.rstrip(chr(92))))
        while self.disk_table_container.count():
            w = self.disk_table_container.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.disk_table_container.addWidget(DiskTable(self.partitions))

        self.combo_dest.blockSignals(True)
        self.combo_dest.clear()
        for p in self.partitions:
            self.combo_dest.addItem(p.mountpoint.rstrip("\\"))

        best = find_best_destination(self.partitions, self.system_disk)
        self.lbl_warning.setVisible(False)

        if best:
            idx = self.combo_dest.findText(best.mountpoint.rstrip("\\"))
            if idx >= 0:
                self.combo_dest.setCurrentIndex(idx)
        elif self.partitions:
            self.combo_dest.setCurrentIndex(0)
            self.lbl_warning.setText(tr("prepare.warn_no_other_disk"))
            self.lbl_warning.setProperty("cssClass", "warning")
            self.lbl_warning.setVisible(True)
            self.lbl_warning.style().unpolish(self.lbl_warning)
            self.lbl_warning.style().polish(self.lbl_warning)

        if len(self.partitions) == 1 and self.partitions[0].free < 1_000_000_000:
            self.lbl_warning.setText(tr("prepare.warn_no_disk"))
            self.lbl_warning.setProperty("cssClass", "error")
            self.lbl_warning.setVisible(True)
            self.lbl_warning.style().unpolish(self.lbl_warning)
            self.lbl_warning.style().polish(self.lbl_warning)

        self.combo_dest.blockSignals(False)
        self.edit_folder.setText(f"{self.combo_dest.currentText()}\\recover")
        self.edit_session.setText(f"Восстановление {datetime.datetime.now().strftime('%d.%m.%Y')}")

        self._check_local_risks()

    def _check_local_risks(self):
        """Сканирует игры и хранилища Obsidian в фоне и обновляет блоки предупреждений."""
        def _scan():
            try:
                games = scan_games_on_system_drive(self.system_disk)
            except Exception:
                games = []
            try:
                vaults = scan_obsidian_vaults(self.system_disk)
            except Exception:
                vaults = []
            self._games_scan_result = games
            self._vaults_scan_result = vaults
            self._local_risks_signal.finished.emit()

        self._local_risks_signal = _ScanSignals()
        self._local_risks_signal.finished.connect(self._on_local_risks_scanned)
        threading.Thread(target=_scan, daemon=True).start()

    def _on_local_risks_scanned(self):
        """Вызывается в основном потоке после завершения сканирования рисков."""
        self._on_games_scanned()
        self._on_vaults_scanned()

    def _on_games_scanned(self):
        games: list[GameInfo] = getattr(self, "_games_scan_result", [])
        if not games:
            self.games_warn_widget.setVisible(False)
            return
        total_size = sum(g.size_bytes for g in games)
        size_str = format_size(total_size) if total_size > 0 else f"{len(games)} шт."
        self.lbl_games_warn.setText(
            tr("prepare.games.warn", disk=self.system_disk.rstrip(chr(92)), count=len(games), size=size_str)
        )
        self.games_tree.setSortingEnabled(False)
        self.games_tree.clear()
        for g in games:
            item = QTreeWidgetItem()
            item.setText(0, g.name)
            item.setText(1, g.launcher)
            item.setText(2, format_size(g.size_bytes) if g.size_bytes > 0 else "—")
            self.games_tree.addTopLevelItem(item)
        self.games_tree.setSortingEnabled(True)
        self.games_warn_widget.setVisible(True)
        self.lbl_games_warn.style().unpolish(self.lbl_games_warn)
        self.lbl_games_warn.style().polish(self.lbl_games_warn)

    def _on_vaults_scanned(self):
        vaults: list[VaultInfo] = getattr(self, "_vaults_scan_result", [])
        if not vaults:
            self.vaults_warn_widget.setVisible(False)
            return
        total_size = sum(v.size_bytes for v in vaults)
        size_str = f", ~{format_size(total_size)}" if total_size > 0 else ""
        plural = tr("prepare.vaults.singular") if len(vaults) == 1 else (
            tr("prepare.vaults.few") if len(vaults) <= 4 else tr("prepare.vaults.many")
        )
        self.lbl_vaults_warn.setText(
            tr("prepare.vaults.warn_text",
               count=len(vaults), plural=plural, size=size_str,
               disk=self.system_disk.rstrip(chr(92)))
        )
        self.vaults_tree.setSortingEnabled(False)
        self.vaults_tree.clear()
        for v in vaults:
            item = QTreeWidgetItem()
            item.setText(0, v.name)
            item.setText(1, v.path)
            item.setText(2, format_size(v.size_bytes) if v.size_bytes > 0 else "—")
            self.vaults_tree.addTopLevelItem(item)
        self.vaults_tree.setSortingEnabled(True)
        self.vaults_warn_widget.setVisible(True)
        self.lbl_vaults_warn.style().unpolish(self.lbl_vaults_warn)
        self.lbl_vaults_warn.style().polish(self.lbl_vaults_warn)

    def _toggle_games_list(self):
        visible = self.games_list_widget.isVisible()
        self.games_list_widget.setVisible(not visible)
        self.btn_games_toggle.setText(
            tr("prepare.games.hide") if not visible else tr("prepare.games.show")
        )

    def _toggle_vaults_list(self):
        visible = self.vaults_list_widget.isVisible()
        self.vaults_list_widget.setVisible(not visible)
        self.btn_vaults_toggle.setText(
            tr("prepare.vaults.hide") if not visible else tr("prepare.vaults.show")
        )

    def _on_dest_changed(self, value):
        self.edit_folder.setText(f"{value}\\recover")

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, tr("prepare.dlg_choose_folder"), self.combo_dest.currentText())
        if path:
            self.edit_folder.setText(path)

    # ═══ ШАГ 2: Поиск файлов ═══════════════════════════
    def _build_step2(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch()
        lbl = QLabel(tr("prepare.scan.idle"))
        lbl.setProperty("cssClass", "subtitle")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        btn_find = QPushButton(tr("prepare.scan.btn"))
        btn_find.setProperty("cssClass", "primary")
        btn_find.setFixedSize(220, 44)
        btn_find.clicked.connect(self._show_search_dialog)
        layout.addWidget(btn_find, alignment=Qt.AlignCenter)

        self.scan_widget = QWidget()
        scan_layout = QVBoxLayout(self.scan_widget)
        self.scan_lbl = QLabel(tr("prepare.scan.running"))
        self.scan_lbl.setAlignment(Qt.AlignCenter)
        scan_layout.addWidget(self.scan_lbl)
        self.scan_bar = QProgressBar()
        self.scan_bar.setRange(0, 0)
        self.scan_bar.setFixedWidth(400)
        scan_layout.addWidget(self.scan_bar, alignment=Qt.AlignCenter)
        self.scan_current = QLabel("")
        self.scan_current.setProperty("cssClass", "muted")
        self.scan_current.setAlignment(Qt.AlignCenter)
        self.scan_current.setWordWrap(True)
        scan_layout.addWidget(self.scan_current)
        self.scan_widget.setVisible(False)
        layout.addWidget(self.scan_widget)

        layout.addStretch()
        self.step_container.addWidget(widget)
        self._step_widgets.append(widget)

    def _show_search_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("prepare.scan.dlg_title"))
        dialog.setFixedSize(400, 270)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(tr("prepare.scan.dlg_header")))
        layout.addSpacing(8)
        cb_configs = QCheckBox(tr("prepare.scan.cb_configs"))
        cb_configs.setChecked(True)
        layout.addWidget(cb_configs)
        cb_personal = QCheckBox(tr("prepare.scan.cb_personal"))
        layout.addWidget(cb_personal)
        cb_programs = QCheckBox(tr("prepare.scan.cb_programs"))
        cb_programs.setChecked(True)
        layout.addWidget(cb_programs)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("prepare.scan.btn_cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)
        btn_start = QPushButton(tr("prepare.scan.btn_start"))
        btn_start.setProperty("cssClass", "primary")
        btn_start.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_start)
        layout.addLayout(btn_row)

        if dialog.exec() == QDialog.Accepted:
            if not cb_configs.isChecked() and not cb_personal.isChecked() and not cb_programs.isChecked():
                QMessageBox.warning(self, tr("prepare.warn_title"), tr("prepare.scan.warn_empty"))
                return
            self._start_scan(cb_configs.isChecked(), cb_personal.isChecked(), cb_programs.isChecked())

    def _start_scan(self, scan_configs: bool, scan_personal: bool, scan_programs: bool = False):
        logger.info("[PrepareScreen] Запуск сканирования: configs=%s, personal=%s, programs=%s",
                    scan_configs, scan_personal, scan_programs)
        self._cancel_scan = False
        self._scan_personal = scan_personal
        self._scan_programs = scan_programs
        self.found_configs.clear()
        self.found_personal.clear()
        self.found_programs.clear()
        self.scan_widget.setVisible(True)

        self._scan_signals = _ScanSignals()
        self._scan_signals.progress.connect(self._update_scan_label)
        self._scan_signals.finished.connect(self._scan_done)

        def _scan():
            logger.info("[scan thread] Запущен")
            username = get_username()
            if scan_configs:
                self.found_configs = scan_appdata(
                    username,
                    progress_callback=lambda p: self._scan_signals.progress.emit(p),
                    cancel_check=lambda: self._cancel_scan,
                )
                logger.info("[scan thread] Конфигов: %d", len(self.found_configs))
                # SSH-ключи добавляем вместе с конфигами
                if not self._cancel_scan:
                    self._scan_signals.progress.emit("Поиск SSH-ключей...")
                    ssh_items = scan_ssh_keys()
                    self.found_configs.extend(ssh_items)
                    logger.info("[scan thread] SSH-файлов: %d", len(ssh_items))
            if scan_personal and not self._cancel_scan:
                self.found_personal = scan_personal_files(
                    username,
                    progress_callback=lambda p: self._scan_signals.progress.emit(p),
                    cancel_check=lambda: self._cancel_scan,
                )
                logger.info("[scan thread] Личных: %d", len(self.found_personal))
            if scan_programs and not self._cancel_scan:
                self._scan_signals.progress.emit("Чтение реестра установленных программ...")
                self.found_programs = scan_installed_programs()
                logger.info("[scan thread] Программ: %d", len(self.found_programs))
            self._scan_signals.finished.emit()

        threading.Thread(target=_scan, daemon=True).start()

    def _update_scan_label(self, path: str):
        short = path if len(path) <= 75 else "..." + path[-72:]
        self.scan_current.setText(short)

    def _scan_done(self):
        logger.info("[PrepareScreen] Сканирование завершено: configs=%d, personal=%d, programs=%d",
                    len(self.found_configs), len(self.found_personal), len(self.found_programs))
        self.scan_widget.setVisible(False)
        total = len(self.found_configs) + len(self.found_personal) + len(self.found_programs)
        if total == 0:
            QMessageBox.information(self, tr("prepare.warn_title"), tr("prepare.scan.nothing_found"))
            return
        self._populate_step3(self._scan_personal, getattr(self, "_scan_programs", False))
        self._show_step(2)

    # ═══ ШАГ 3: Выбор файлов ═══════════════════════════
    def _build_step3(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.step3_tabs = QTabWidget()
        layout.addWidget(self.step3_tabs, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_add = QPushButton(tr("prepare.s3.btn_add"))
        self.btn_add.setProperty("cssClass", "success")
        self.btn_add.setFixedSize(220, 38)
        self.btn_add.clicked.connect(self._add_selected)
        btn_row.addWidget(self.btn_add)
        layout.addLayout(btn_row)
        self.step_container.addWidget(widget)
        self._step_widgets.append(widget)

    def _populate_step3(self, has_personal: bool, has_programs: bool = False):
        self.step3_tabs.clear()

        # ── Конфиги ──────────────────────────────────────────────────────
        tab_cfg = QWidget()
        lo = QVBoxLayout(tab_cfg)
        lo.setContentsMargins(4, 4, 4, 4)

        # Кнопки выделения
        top = QHBoxLayout()
        b1 = QPushButton(tr("prepare.s3.btn_all"))
        b1.clicked.connect(lambda: self.config_tree.select_all())
        top.addWidget(b1)
        b2 = QPushButton(tr("prepare.s3.btn_none"))
        b2.clicked.connect(lambda: self.config_tree.deselect_all())
        top.addWidget(b2)
        b_sel_cfg = QPushButton(tr("prepare.s3.btn_configs"))
        b_sel_cfg.clicked.connect(lambda: self.config_tree.select_by_type("Конфиг"))
        top.addWidget(b_sel_cfg)
        b_sel_other = QPushButton(tr("prepare.s3.btn_other"))
        b_sel_other.clicked.connect(lambda: self.config_tree.select_by_type("Другое"))
        top.addWidget(b_sel_other)
        b_sel_rec = QPushButton(tr("prepare.s3.btn_rec"))
        b_sel_rec.setProperty("cssClass", "success")
        b_sel_rec.setToolTip(tr("prepare.s3.btn_rec_tip"))
        b_sel_rec.clicked.connect(lambda: self.config_tree.select_recommended())
        top.addWidget(b_sel_rec)
        top.addStretch()
        b3 = QPushButton(tr("prepare.s3.btn_folder"))
        b3.clicked.connect(self._add_custom_config_folder)
        top.addWidget(b3)
        lo.addLayout(top)

        # Строка поиска + разворачивание
        search_row = QHBoxLayout()
        self._search_config = QLineEdit()
        self._search_config.setPlaceholderText(tr("prepare.s3.search_configs"))
        self._search_config.setClearButtonEnabled(True)
        search_row.addWidget(self._search_config, 1)
        btn_expand = QPushButton(tr("prepare.s3.btn_expand"))
        btn_expand.setProperty("cssClass", "flat")
        btn_expand.setFixedWidth(130)
        btn_collapse = QPushButton(tr("prepare.s3.btn_collapse"))
        btn_collapse.setProperty("cssClass", "flat")
        btn_collapse.setFixedWidth(130)
        search_row.addWidget(btn_expand)
        search_row.addWidget(btn_collapse)
        lo.addLayout(search_row)

        self.config_tree = FileTreeWidget(item_type="config")
        self._search_config.textChanged.connect(self.config_tree.filter_items)
        btn_expand.clicked.connect(self.config_tree.expandAll)
        btn_collapse.clicked.connect(self.config_tree.collapseAll)
        lo.addWidget(self.config_tree, 1)

        # Статус-бар
        self._lbl_config_status = QLabel(tr("prepare.s3.status_empty"))
        self._lbl_config_status.setProperty("cssClass", "muted")
        lo.addWidget(self._lbl_config_status)
        self.config_tree.selection_changed.connect(self._update_config_status)

        # Наполняем дерево конфигов
        for item in sorted(self.found_configs, key=lambda x: x.name.lower()):
            self.config_tree.add_item(
                name=item.name, path=str(item.path), size=item.size, is_dir=item.is_dir,
                data={"source_path": str(item.path), "relative_path": item.relative_path,
                      "size_bytes": item.size, "is_dir": item.is_dir, "type": "config", "name": item.name},
                content_type=item.content_type, children=item.children,
                location=item.location,
                priority=item.priority,
                priority_reason=item.priority_reason,
            )

        # Предупреждение о дубликатах (Local + Roaming)
        locations_by_name: dict[str, set[str]] = {}
        for fi in self.found_configs:
            if fi.location:
                locations_by_name.setdefault(fi.name, set()).add(fi.location)
        duplicates = [n for n, locs in locations_by_name.items() if len(locs) > 1]
        if duplicates:
            dup_names = ", ".join(duplicates[:6])
            if len(duplicates) > 6:
                dup_names += tr("prepare.s3.warn_dup_more", n=len(duplicates) - 6)
            warn_lbl = QLabel(tr("prepare.s3.warn_dup", names=dup_names))
            warn_lbl.setProperty("cssClass", "warning")
            warn_lbl.setWordWrap(True)
            lo.addWidget(warn_lbl)
            # Обновляем стиль
            warn_lbl.style().unpolish(warn_lbl)
            warn_lbl.style().polish(warn_lbl)

        self._update_config_status()
        self.step3_tabs.addTab(tab_cfg, tr("prepare.s3.tab_configs", count=len(self.found_configs)))

        # ── Личные файлы ─────────────────────────────────────────────────
        self.personal_tree = None
        if has_personal and self.found_personal:
            tab_per = QWidget()
            lo2 = QVBoxLayout(tab_per)
            lo2.setContentsMargins(4, 4, 4, 4)

            top2 = QHBoxLayout()
            bp1 = QPushButton(tr("prepare.s3.btn_all"))
            bp1.clicked.connect(lambda: self.personal_tree.select_all())
            top2.addWidget(bp1)
            bp2 = QPushButton(tr("prepare.s3.btn_none"))
            bp2.clicked.connect(lambda: self.personal_tree.deselect_all())
            top2.addWidget(bp2)
            lbl_group = QLabel(tr("prepare.s3.prog_group"))
            lbl_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top2.addWidget(lbl_group)
            self._combo_grouping = QComboBox()
            self._combo_grouping.addItems([
                tr("prepare.s3.group_folder"),
                tr("prepare.s3.group_type"),
                tr("prepare.s3.group_folder_type"),
                tr("prepare.s3.group_flat"),
            ])
            self._combo_grouping.setFixedWidth(190)
            self._combo_grouping.currentIndexChanged.connect(self._on_grouping_changed)
            top2.addWidget(self._combo_grouping)
            top2.addStretch()
            bp3 = QPushButton(tr("prepare.s3.btn_add_files"))
            bp3.clicked.connect(self._add_custom_personal_files)
            top2.addWidget(bp3)
            bp4 = QPushButton(tr("prepare.s3.btn_add_folder"))
            bp4.clicked.connect(self._add_custom_personal_folder)
            top2.addWidget(bp4)
            lo2.addLayout(top2)

            # Поиск для личных файлов
            self._search_personal = QLineEdit()
            self._search_personal.setPlaceholderText(tr("prepare.s3.search_personal"))
            self._search_personal.setClearButtonEnabled(True)
            lo2.addWidget(self._search_personal)

            self.personal_tree = FileTreeWidget(item_type="personal")
            self._search_personal.textChanged.connect(self.personal_tree.filter_items)
            lo2.addWidget(self.personal_tree, 1)

            # Статус-бар
            self._lbl_personal_status = QLabel(tr("prepare.s3.status_empty"))
            self._lbl_personal_status.setProperty("cssClass", "muted")
            lo2.addWidget(self._lbl_personal_status)
            self.personal_tree.selection_changed.connect(self._update_personal_status)

            self._rebuild_personal_tree()
            self.step3_tabs.addTab(tab_per, tr("prepare.s3.tab_personal", count=len(self.found_personal)))

        # ── Программы ────────────────────────────────────────────────────
        if has_programs and self.found_programs:
            self._build_programs_tab(self.step3_tabs, self.found_programs, review=False)

    def _build_programs_tab(self, tab_widget: QTabWidget,
                            programs: list, review: bool = False):
        """Строит вкладку со списком программ для шага 3 или 4."""
        from collections import defaultdict

        tab = QWidget()
        lo = QVBoxLayout(tab)
        lo.setContentsMargins(4, 4, 4, 4)

        # ── Дерево ───────────────────────────────────────────────────────
        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels([tr("prepare.s3.prog_col_name"), tr("prepare.s3.prog_col_pub"), tr("prepare.s3.prog_col_ver"), tr("prepare.s3.prog_col_date")])
        tree.setAlternatingRowColors(True)
        tree.setSortingEnabled(True)
        tree.setRootIsDecorated(not review)
        hdr = tree.header()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(False)
        tree.setColumnWidth(0, 260)
        tree.setColumnWidth(1, 180)
        tree.setColumnWidth(2, 100)
        tree.setColumnWidth(3, 100)

        if review:
            # Только просмотр — плоский список без чекбоксов
            for prog in programs:
                item = QTreeWidgetItem()
                item.setText(0, prog.name)
                item.setText(1, prog.publisher)
                item.setText(2, prog.version)
                item.setText(3, prog.install_date_fmt)
                tree.addTopLevelItem(item)
            lo.addWidget(tree, 1)
            tab_widget.addTab(tab, tr("prepare.s3.tab_programs", count=len(programs)))
            return

        # ── Интерактивный режим (шаг 3) ──────────────────────────────────

        # Строка 1: кнопки + группировка
        ctrl_row = QHBoxLayout()
        btn_all = QPushButton(tr("prepare.s3.prog_all"))
        btn_none = QPushButton(tr("prepare.s3.prog_none"))
        ctrl_row.addWidget(btn_all)
        ctrl_row.addWidget(btn_none)
        ctrl_row.addStretch()
        ctrl_row.addWidget(QLabel(tr("prepare.s3.prog_group")))
        combo_group = QComboBox()
        combo_group.addItems([tr("prepare.s3.prog_grouped"), tr("prepare.s3.prog_flat")])
        combo_group.setFixedWidth(175)
        ctrl_row.addWidget(combo_group)
        lo.addLayout(ctrl_row)

        # Строка 2: поиск + быстрые кнопки снятия
        quick_row = QHBoxLayout()
        search_prog = QLineEdit()
        search_prog.setPlaceholderText(tr("prepare.s3.prog_search"))
        search_prog.setClearButtonEnabled(True)
        quick_row.addWidget(search_prog, 1)
        quick_row.addSpacing(6)
        quick_row.addWidget(QLabel(tr("prepare.s3.prog_deselect")))
        _quick_cats = [
            (tr("prepare.s3.prog_drivers"), "🔧 Драйверы"),
            (tr("prepare.s3.prog_ms"),      "🏢 Microsoft"),
            (tr("prepare.s3.prog_sys"),     "📦 Системные"),
        ]
        for btn_label, cat_name in _quick_cats:
            btn_q = QPushButton(btn_label)
            btn_q.setProperty("cssClass", "flat")
            btn_q.clicked.connect(lambda checked=False, c=cat_name: _deselect_category(c))
            quick_row.addWidget(btn_q)
        lo.addLayout(quick_row)

        lo.addWidget(tree, 1)

        # Статус-бар
        lbl_status = QLabel()
        lbl_status.setProperty("cssClass", "muted")
        lo.addWidget(lbl_status)

        # Подсказка об авто-снятии
        lbl_hint = QLabel(tr("prepare.s3.prog_hint"))
        lbl_hint.setWordWrap(True)
        lbl_hint.setProperty("cssClass", "muted")
        lo.addWidget(lbl_hint)

        # ── Логика ───────────────────────────────────────────────────────
        propagating = [False]

        def _update_status():
            checked = total = 0
            for i in range(tree.topLevelItemCount()):
                top = tree.topLevelItem(i)
                if top.isHidden():
                    continue
                if top.childCount():
                    for j in range(top.childCount()):
                        child = top.child(j)
                        if not child.isHidden():
                            total += 1
                            if child.checkState(0) == Qt.Checked:
                                checked += 1
                else:
                    total += 1
                    if top.checkState(0) == Qt.Checked:
                        checked += 1
            lbl_status.setText(tr("prepare.s3.prog_status", checked=checked, total=total))

        def _on_item_changed(item, col):
            if col != 0 or propagating[0]:
                return
            propagating[0] = True
            try:
                # Родитель изменён → распространить на детей
                if item.childCount():
                    state = item.checkState(0)
                    if state != Qt.PartiallyChecked:
                        for j in range(item.childCount()):
                            item.child(j).setCheckState(0, state)
                # Ребёнок изменён → обновить родителя
                parent = item.parent()
                if parent is not None:
                    children = [parent.child(j) for j in range(parent.childCount())]
                    n_checked = sum(1 for c in children if c.checkState(0) == Qt.Checked)
                    n_partial = sum(1 for c in children if c.checkState(0) == Qt.PartiallyChecked)
                    if n_checked == 0 and n_partial == 0:
                        parent.setCheckState(0, Qt.Unchecked)
                    elif n_checked == len(children):
                        parent.setCheckState(0, Qt.Checked)
                    else:
                        parent.setCheckState(0, Qt.PartiallyChecked)
            finally:
                propagating[0] = False
            _update_status()

        tree.itemChanged.connect(_on_item_changed)

        # Категории, которые переустанавливаются автоматически — не рекомендуем сохранять
        _SKIP_CATS = {"🔧 Драйверы", "📦 Системные", "🏢 Microsoft"}
        _COLOR_SKIP = QColor("#888888")

        def _make_prog_item(prog, indent: bool = False) -> QTreeWidgetItem:
            is_skip = prog.category in _SKIP_CATS
            item = QTreeWidgetItem()
            prefix = "    " if indent else ""
            if is_skip:
                display = f"{prefix}💤  {prog.name}"
                tip = tr("prepare.s3.prog_skip_tip")
            else:
                display = f"{prefix}⭐  {prog.name}"
                tip = tr("prepare.s3.prog_rec_tip")
            item.setText(0, display)
            item.setText(1, prog.publisher)
            item.setText(2, prog.version)
            item.setText(3, prog.install_date_fmt)
            item.setToolTip(0, tip)
            item.setCheckState(0, Qt.Unchecked if is_skip else Qt.Checked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setData(0, Qt.UserRole, prog)
            if is_skip:
                for col in range(tree.columnCount()):
                    item.setForeground(col, _COLOR_SKIP)
            return item

        def _populate_tree(grouped: bool):
            tree.setSortingEnabled(False)
            propagating[0] = True
            tree.clear()
            if grouped:
                groups: dict[str, list] = defaultdict(list)
                for prog in programs:
                    groups[prog.category].append(prog)

                def _cat_order(c: str) -> int:
                    try:
                        return CATEGORIES_ORDER.index(c)
                    except ValueError:
                        return 999

                for cat in sorted(groups.keys(), key=_cat_order):
                    entries = groups[cat]
                    is_skip_cat = cat in _SKIP_CATS
                    hdr_item = QTreeWidgetItem()
                    hdr_item.setText(0, cat)
                    hdr_item.setText(1, tr("prepare.s3.prog_count", count=len(entries)))
                    hdr_item.setCheckState(0, Qt.Unchecked if is_skip_cat else Qt.Checked)
                    hdr_item.setFlags(hdr_item.flags() | Qt.ItemIsUserCheckable)
                    if is_skip_cat:
                        for col in range(tree.columnCount()):
                            hdr_item.setForeground(col, _COLOR_SKIP)
                    tree.addTopLevelItem(hdr_item)
                    for prog in sorted(entries, key=lambda p: p.name.lower()):
                        hdr_item.addChild(_make_prog_item(prog, indent=True))
                    hdr_item.setExpanded(False)
            else:
                for prog in programs:
                    tree.addTopLevelItem(_make_prog_item(prog))

            propagating[0] = False
            tree.setSortingEnabled(True)
            _update_status()

        def _filter(text: str):
            tl = text.lower()
            is_grouped = combo_group.currentIndex() == 0
            if is_grouped:
                for i in range(tree.topLevelItemCount()):
                    top = tree.topLevelItem(i)
                    any_visible = False
                    for j in range(top.childCount()):
                        child = top.child(j)
                        match = not tl or tl in child.text(0).lower() or tl in child.text(1).lower()
                        child.setHidden(not match)
                        if match:
                            any_visible = True
                    top.setHidden(not any_visible)
            else:
                for i in range(tree.topLevelItemCount()):
                    it = tree.topLevelItem(i)
                    match = not tl or tl in it.text(0).lower() or tl in it.text(1).lower()
                    it.setHidden(not match)
            _update_status()

        def _select_all():
            propagating[0] = True
            try:
                for i in range(tree.topLevelItemCount()):
                    top = tree.topLevelItem(i)
                    if not top.isHidden():
                        top.setCheckState(0, Qt.Checked)
                        for j in range(top.childCount()):
                            if not top.child(j).isHidden():
                                top.child(j).setCheckState(0, Qt.Checked)
            finally:
                propagating[0] = False
            _update_status()

        def _deselect_all():
            propagating[0] = True
            try:
                for i in range(tree.topLevelItemCount()):
                    top = tree.topLevelItem(i)
                    if not top.isHidden():
                        top.setCheckState(0, Qt.Unchecked)
                        for j in range(top.childCount()):
                            if not top.child(j).isHidden():
                                top.child(j).setCheckState(0, Qt.Unchecked)
            finally:
                propagating[0] = False
            _update_status()

        def _deselect_category(cat_name: str):
            is_grouped = combo_group.currentIndex() == 0
            propagating[0] = True
            try:
                if is_grouped:
                    for i in range(tree.topLevelItemCount()):
                        top = tree.topLevelItem(i)
                        if top.text(0) == cat_name:
                            top.setCheckState(0, Qt.Unchecked)
                            for j in range(top.childCount()):
                                top.child(j).setCheckState(0, Qt.Unchecked)
                else:
                    for i in range(tree.topLevelItemCount()):
                        it = tree.topLevelItem(i)
                        prog = it.data(0, Qt.UserRole)
                        if prog and prog.category == cat_name:
                            it.setCheckState(0, Qt.Unchecked)
            finally:
                propagating[0] = False
            _update_status()

        def _on_grouping_changed():
            search_prog.blockSignals(True)
            search_prog.clear()
            search_prog.blockSignals(False)
            _populate_tree(combo_group.currentIndex() == 0)

        btn_all.clicked.connect(_select_all)
        btn_none.clicked.connect(_deselect_all)
        search_prog.textChanged.connect(_filter)
        combo_group.currentIndexChanged.connect(lambda: _on_grouping_changed())

        # Сохраняем ссылки для сбора выбранного в _add_selected
        self._programs_tree = tree
        self._programs_grouped_combo = combo_group

        _populate_tree(True)  # по умолчанию — по категориям

        tab_widget.addTab(tab, tr("prepare.s3.tab_programs", count=len(programs)))

    # Режим → параметр group_by
    _GROUPING_MODES = ["folder", "type", "folder+type", "flat"]

    def _on_grouping_changed(self, index: int):
        self._rebuild_personal_tree()

    def _rebuild_personal_tree(self):
        """Перестраивает дерево личных файлов в выбранном режиме группировки."""
        if not self.personal_tree:
            return
        # Сбросить поиск при перестройке
        if hasattr(self, "_search_personal"):
            self._search_personal.blockSignals(True)
            self._search_personal.clear()
            self._search_personal.blockSignals(False)
        self.personal_tree.clear()
        entries = [
            {"source_path": str(item.path), "relative_path": item.relative_path,
             "size_bytes": item.size, "is_dir": item.is_dir, "type": "personal", "name": item.name}
            for item in sorted(self.found_personal, key=lambda x: x.name.lower())
        ]
        idx = self._combo_grouping.currentIndex() if hasattr(self, "_combo_grouping") else 0
        mode = self._GROUPING_MODES[idx]
        if mode == "flat":
            for e in entries:
                self.personal_tree.add_item(
                    name=e["name"], path=e["source_path"], size=e["size_bytes"],
                    is_dir=e["is_dir"], data=e,
                )
        else:
            self.personal_tree.add_grouped_items(entries, group_by=mode)
            self.personal_tree.expandToDepth(0)
        self._update_personal_status()

    def _update_config_status(self):
        if not hasattr(self, "_lbl_config_status") or not hasattr(self, "config_tree"):
            return
        sel, total, sel_size, tot_size = self.config_tree.get_stats()
        if sel == 0:
            self._lbl_config_status.setText(tr("prepare.s3.status_zero", total=total))
        else:
            self._lbl_config_status.setText(
                tr("prepare.s3.status", sel=sel, total=total,
                   sel_size=format_size(sel_size), tot_size=format_size(tot_size))
            )

    def _update_personal_status(self):
        if not hasattr(self, "_lbl_personal_status") or not self.personal_tree:
            return
        sel, total, sel_size, tot_size = self.personal_tree.get_stats()
        if sel == 0:
            self._lbl_personal_status.setText(tr("prepare.s3.status_zero", total=total))
        else:
            self._lbl_personal_status.setText(
                tr("prepare.s3.status", sel=sel, total=total,
                   sel_size=format_size(sel_size), tot_size=format_size(tot_size))
            )

    def _add_custom_config_folder(self):
        path = QFileDialog.getExistingDirectory(self, tr("prepare.dlg_folder"))
        if not path:
            return
        p = Path(path)
        from core.file_scanner import _dir_size, _classify_dir
        size = _dir_size(p)
        content_type, children = _classify_dir(p)
        user_dir = Path.home()
        try:
            rel = str(p.relative_to(user_dir))
        except ValueError:
            rel = str(p)
        self.config_tree.add_item(
            name=p.name, path=str(p), size=size, is_dir=True,
            data={"source_path": str(p), "relative_path": rel, "size_bytes": size,
                  "is_dir": True, "type": "config", "name": p.name},
            content_type=content_type, children=children,
        )

    def _add_custom_personal_folder(self):
        path = QFileDialog.getExistingDirectory(self, tr("prepare.dlg_folder2"))
        if not path or not self.personal_tree:
            return
        p = Path(path)
        from core.file_scanner import _dir_size
        size = _dir_size(p)
        user_dir = Path.home()
        try:
            rel = str(p.relative_to(user_dir))
        except ValueError:
            rel = str(p)
        self.personal_tree.add_item(
            name=p.name, path=str(p), size=size, is_dir=True,
            data={"source_path": str(p), "relative_path": rel, "size_bytes": size,
                  "is_dir": True, "type": "personal", "name": p.name},
        )

    def _add_custom_personal_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("prepare.dlg_files"))
        if not files or not self.personal_tree:
            return
        user_dir = Path.home()
        for fpath in files:
            p = Path(fpath)
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            try:
                rel = str(p.relative_to(user_dir))
            except ValueError:
                rel = str(p)
            self.personal_tree.add_item(
                name=p.name, path=str(p), size=size, is_dir=False,
                data={"source_path": str(p), "relative_path": rel, "size_bytes": size,
                      "is_dir": False, "type": "personal", "name": p.name},
            )

    def _add_selected(self):
        self.added_entries.clear()
        self.added_entries.extend(self.config_tree.get_selected_data())
        if self.personal_tree:
            self.added_entries.extend(self.personal_tree.get_selected_data())

        # Собрать выбранные программы
        self.selected_programs.clear()
        if hasattr(self, "_programs_tree"):
            tree = self._programs_tree
            is_grouped = (hasattr(self, "_programs_grouped_combo")
                          and self._programs_grouped_combo.currentIndex() == 0)
            if is_grouped:
                for i in range(tree.topLevelItemCount()):
                    top = tree.topLevelItem(i)
                    for j in range(top.childCount()):
                        child = top.child(j)
                        if child.checkState(0) == Qt.Checked:
                            prog = child.data(0, Qt.UserRole)
                            if prog:
                                self.selected_programs.append(prog)
            else:
                for i in range(tree.topLevelItemCount()):
                    it = tree.topLevelItem(i)
                    if it.checkState(0) == Qt.Checked:
                        prog = it.data(0, Qt.UserRole)
                        if prog:
                            self.selected_programs.append(prog)

        logger.info("[PrepareScreen] Выбрано: %d файлов, %d программ",
                    len(self.added_entries), len(self.selected_programs))
        if not self.added_entries and not self.selected_programs:
            QMessageBox.warning(self, tr("prepare.warn_title"), tr("prepare.warn_pick_one"))
            return
        self._populate_step4()
        self._show_step(3)

    # ═══ ШАГ 4: Обзор и запуск ═════════════════════════
    def _build_step4(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.step4_tabs = QTabWidget()
        layout.addWidget(self.step4_tabs, 1)

        self.lbl_summary = QLabel()
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel(tr("prepare.s4.mode")))
        self.radio_copy = QRadioButton(tr("prepare.s4.mode_copy"))
        self.radio_copy.setChecked(True)
        self.radio_archive = QRadioButton(tr("prepare.s4.mode_archive"))
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_copy, 0)
        self.mode_group.addButton(self.radio_archive, 1)
        mode_row.addWidget(self.radio_copy)
        mode_row.addWidget(self.radio_archive)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_create = QPushButton(tr("prepare.s4.btn_create"))
        btn_create.setProperty("cssClass", "success")
        btn_create.setFixedSize(320, 42)
        btn_create.clicked.connect(self._start_copy)
        btn_row.addWidget(btn_create)
        layout.addLayout(btn_row)

        self.step_container.addWidget(widget)
        self._step_widgets.append(widget)

    def _populate_step4(self):
        self.step4_tabs.clear()
        configs = [e for e in self.added_entries if e["type"] == "config"]
        personal = [e for e in self.added_entries if e["type"] == "personal"]

        self._review_config_tree = None
        self._review_personal_tree = None

        if configs:
            tab = QWidget()
            tl = QVBoxLayout(tab)
            tl.setContentsMargins(4, 4, 4, 4)
            self._review_config_tree = FileTreeWidget(item_type="config")
            for e in configs:
                self._review_config_tree.add_item(
                    name=e.get("name", Path(e["source_path"]).name),
                    path=e["source_path"], size=e["size_bytes"], is_dir=e["is_dir"], data=e,
                )
            self._review_config_tree.select_all()
            tl.addWidget(self._review_config_tree)
            self.step4_tabs.addTab(tab, tr("prepare.s4.tab_configs", count=len(configs)))

        if personal:
            tab = QWidget()
            tl = QVBoxLayout(tab)
            tl.setContentsMargins(4, 4, 4, 4)
            self._review_personal_tree = FileTreeWidget(item_type="personal")
            self._review_personal_tree.add_grouped_items(personal)
            self._review_personal_tree.select_all()
            self._review_personal_tree.expandAll()
            tl.addWidget(self._review_personal_tree)
            self.step4_tabs.addTab(tab, tr("prepare.s4.tab_personal", count=len(personal)))

        if self.selected_programs:
            self._build_programs_tab(self.step4_tabs, self.selected_programs, review=True)

        total_size = sum(e["size_bytes"] for e in self.added_entries)
        dest_disk = self.combo_dest.currentText() + "\\"
        try:
            free = psutil.disk_usage(dest_disk).free
        except Exception:
            free = 0
        prog_part = tr("prepare.s4.summary_progs", count=len(self.selected_programs)) if self.selected_programs else ""
        self.lbl_summary.setText(
            tr("prepare.s4.summary",
               configs=len(configs), files=len(personal), programs=prog_part,
               size=format_size(total_size), disk=self.combo_dest.currentText(), free=format_size(free))
        )

    def _start_copy(self):
        logger.info("[PrepareScreen] Запуск копирования...")
        final = []
        if self._review_config_tree:
            final.extend(self._review_config_tree.get_selected_data())
        if self._review_personal_tree:
            final.extend(self._review_personal_tree.get_selected_data())
        if not final and not self.selected_programs:
            QMessageBox.warning(self, tr("prepare.warn_title"), tr("prepare.s4.warn_empty"))
            return

        total_size = sum(e["size_bytes"] for e in final)
        required = int(total_size * 1.1)
        dest_disk = self.combo_dest.currentText() + "\\"
        try:
            free = psutil.disk_usage(dest_disk).free
        except Exception:
            free = 0
        if free < required:
            QMessageBox.critical(self, tr("prepare.s4.space_title"),
                tr("prepare.s4.space_msg",
                   required=format_size(required), free=format_size(free),
                   diff=format_size(required - free)))
            return

        self.added_entries = final
        dest_path = Path(self.edit_folder.text())
        archive_mode = self.radio_archive.isChecked()

        sys_part = next((p for p in self.partitions
                         if p.mountpoint.upper().startswith(self.system_disk.upper())), None)
        config = config_manager.create_default_config(
            destination_folder=str(dest_path), system_disk=self.system_disk,
            system_disk_total=sys_part.total if sys_part else 0,
            system_disk_free=sys_part.free if sys_part else 0,
            old_username=get_username(), session_name=self.edit_session.text(),
            archive_mode=archive_mode,
        )
        for e in final:
            config_manager.add_entry(config, entry_type=e["type"],
                name=e.get("name", Path(e["source_path"]).name),
                source_path=e["source_path"], relative_path=e["relative_path"],
                is_dir=e["is_dir"], size_bytes=e["size_bytes"])

        modal = ProgressModal(self, title=tr("prepare.s4.copy_title"))
        self._copy_signals = _CopySignals()

        def _on_done(results):
            modal.allow_close()
            modal.accept()
            config_manager.save_config(config, dest_path)
            # Сохранить список программ
            if self.selected_programs:
                try:
                    dest_path.mkdir(parents=True, exist_ok=True)
                    md = programs_to_markdown(self.selected_programs)
                    (dest_path / "programs_list.md").write_text(md, encoding="utf-8")
                except Exception as exc:
                    logger.warning("Не удалось сохранить список программ: %s", exc)
            ok = sum(1 for e in results if e.get("status") == "ok")
            err = sum(1 for e in results if e.get("status", "").startswith("error"))
            msg = tr("prepare.s4.done_msg", ok=ok)
            if err:
                msg += tr("prepare.s4.done_errors", err=err)
            if self.selected_programs:
                msg += tr("prepare.s4.done_progs", count=len(self.selected_programs))
            msg += "\n" + tr("prepare.s4.done_path", path=dest_path)
            QMessageBox.information(self, tr("prepare.s4.done_title"), msg)

        self._copy_signals.finished.connect(_on_done)

        def _do_copy():
            def pcb(prog: CopyProgress):
                modal.update_progress(prog.current_file, prog.percent, prog.speed_bps, prog.eta_seconds)
            results = copy_entries(config["entries"], dest_path, archive_mode=archive_mode,
                                   progress_callback=pcb, cancel_check=lambda: modal.cancelled)
            self._copy_signals.finished.emit(results)

        threading.Thread(target=_do_copy, daemon=True).start()
        modal.exec()

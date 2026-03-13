"""Интернационализация — поддержка русского и английского языков."""

import json
import sys
from pathlib import Path

# ─── Настройки ────────────────────────────────────────────────────────────────

_SUPPORTED = ("ru", "en")
_lang: str = "ru"

if getattr(sys, "frozen", False):
    _prefs_file = Path(sys.executable).parent / "preferences.json"
else:
    _prefs_file = Path(__file__).parent.parent / "preferences.json"


def get_language() -> str:
    return _lang


def set_language(lang: str):
    global _lang
    if lang in _SUPPORTED:
        _lang = lang
        _save()


def load_language():
    global _lang
    try:
        if _prefs_file.exists():
            data = json.loads(_prefs_file.read_text(encoding="utf-8"))
            lang = data.get("language", "ru")
            if lang in _SUPPORTED:
                _lang = lang
    except Exception:
        pass


def _save():
    try:
        existing: dict = {}
        if _prefs_file.exists():
            try:
                existing = json.loads(_prefs_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing["language"] = _lang
        _prefs_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        pass


def tr(key: str, **kwargs) -> str:
    """Возвращает переведённую строку. Поддерживает .format(**kwargs)."""
    val = _S.get(_lang, {}).get(key) or _S["ru"].get(key, key)
    if kwargs:
        try:
            return val.format(**kwargs)
        except (KeyError, ValueError):
            return val
    return val


def tr_cat(cat_name: str) -> str:
    """Переводит внутреннее имя категории программ для отображения."""
    if _lang == "en":
        return _CAT_EN.get(cat_name, cat_name)
    return cat_name


# ─── Перевод категорий программ (внутренние ключи остаются русскими) ──────────

_CAT_EN: dict[str, str] = {
    "🔧 Драйверы":        "🔧 Drivers",
    "📦 Системные":       "📦 System Components",
    "🏢 Microsoft":       "🏢 Microsoft",
    "🌐 Браузеры":        "🌐 Browsers",
    "🎮 Игры и лаунчеры": "🎮 Games & Launchers",
    "💻 Разработка":      "💻 Development",
    "🎵 Медиа":           "🎵 Media",
    "🔒 Безопасность":    "🔒 Security",
    "📄 Офис":            "📄 Office",
    "📁 Прочее":          "📁 Other",
}

# ─── Строки ───────────────────────────────────────────────────────────────────

_S: dict[str, dict[str, str]] = {
    "ru": {
        # App
        "app.window_title": "WinRecover — Помощник при переустановке Windows",
        "app.btn_logs":     "📋 Логи",
        "app.btn_lang":     "EN",

        # Start screen
        "start.subtitle":         "Помощник при переустановке Windows",
        "start.btn_prepare.title":"🔄  ПОДГОТОВКА К ПЕРЕУСТАНОВКЕ",
        "start.btn_prepare.desc": "Сохраните настройки и файлы перед\nпереустановкой Windows",
        "start.btn_restore.title":"✅  WINDOWS УЖЕ ПЕРЕУСТАНОВЛЕНА",
        "start.btn_restore.desc": "Восстановите файлы и настройки\nиз резервной копии",
        "start.btn_rec.title":    "💡  РЕКОМЕНДАЦИИ ПРИ ЧИСТОЙ УСТАНОВКЕ",
        "start.btn_rec.desc":     "Полезный софт после переустановки Windows:\nтвики, утилиты, инструменты разработчика",

        # Log window
        "log.title":     "📋 Логи WinRecover",
        "log.waiting":   "Ожидание новых записей...",
        "log.autoscroll":"Автопрокрутка",
        "log.clear":     "Очистить",
        "log.close":     "Закрыть",
        "log.loaded":    "Загружено {count} строк из файла",
        "log.records":   "{count} записей",
        "log.cleared":   "Очищено",

        # Recommendations
        "rec.btn_back": "← Назад",
        "rec.title":    "💡 Рекомендации при чистой установке Windows",
        "rec.hint":     "Список полезных программ, которые стоит установить после чистой инсталляции Windows. "
                        "Нажмите на ссылку рядом с названием, чтобы открыть официальную страницу.",

        # Prepare — navigation
        "prepare.btn_back": "← Назад",
        "prepare.step1":    "Шаг 1 из 4 — Анализ дисков",
        "prepare.step2":    "Шаг 2 из 4 — Поиск файлов",
        "prepare.step3":    "Шаг 3 из 4 — Выбор файлов",
        "prepare.step4":    "Шаг 4 из 4 — Обзор и запуск",
        "prepare.btn_next": "Далее →",

        # Prepare step 1 — disk
        "prepare.system_disk":       "💻 Системный диск: {disk}\n(Windows будет переустановлена сюда)",
        "prepare.partitions":         "Найденные разделы:",
        "prepare.dest_disk":          "Диск назначения:",
        "prepare.dest_folder":        "Папка:",
        "prepare.btn_browse":         "Обзор",
        "prepare.session_name":       "Название сессии:",
        "prepare.dlg_choose_folder":  "Выберите папку",
        "prepare.warn_no_other_disk": "⚠️ Других дисков не найдено. Папка 'recover' будет создана на системном диске.",
        "prepare.warn_no_disk":       "🔴 Подключите внешний накопитель для сохранения данных",

        # Prepare step 1 — games warning
        "prepare.games.col_name": "Название игры",
        "prepare.games.col_plat": "Платформа",
        "prepare.games.col_size": "Размер",
        "prepare.games.tip":      "💡 Перенесите игры на другой диск (D:, E:…) до переустановки — иначе все данные на C: будут удалены вместе с ними.",
        "prepare.games.warn":     "⚠️  На диске {disk} найдены игры: {count} шт., ~{size} — будут удалены при переустановке!",
        "prepare.games.show":     "▼ Показать список",
        "prepare.games.hide":     "▲ Скрыть список",

        # Prepare step 1 — vaults warning
        "prepare.vaults.col_name":  "Хранилище",
        "prepare.vaults.col_path":  "Путь",
        "prepare.vaults.col_size":  "Размер",
        "prepare.vaults.tip":       "💡 Obsidian хранит заметки локально. Добавьте хранилища в копирование через «Добавить свою папку» на шаге 3, или скопируйте вручную.",
        "prepare.vaults.show":      "▼ Показать список",
        "prepare.vaults.hide":      "▲ Скрыть список",
        "prepare.vaults.singular":  "хранилище",
        "prepare.vaults.few":       "хранилища",
        "prepare.vaults.many":      "хранилищ",
        "prepare.vaults.warn_text": "⚠️  Obsidian: найдено {count} {plural}{size} на {disk} — заметки будут удалены при переустановке!",

        # Prepare step 2 — scan
        "prepare.scan.idle":         "Нажмите кнопку для поиска файлов на системном диске",
        "prepare.scan.btn":          "🔍 НАЙТИ ФАЙЛЫ",
        "prepare.scan.running":      "Сканирование...",
        "prepare.scan.dlg_title":    "Что искать?",
        "prepare.scan.dlg_header":   "<b style='font-size:16px'>Что искать?</b>",
        "prepare.scan.cb_configs":   "Конфиги программ (AppData)\nНастройки установленных приложений",
        "prepare.scan.cb_personal":  "Личные файлы\nДокументы, Изображения, Видео, Музыка",
        "prepare.scan.cb_programs":  "Список установленных программ\nЧтобы знать, что переустанавливать после",
        "prepare.scan.btn_cancel":   "Отмена",
        "prepare.scan.btn_start":    "Начать поиск",
        "prepare.scan.warn_empty":   "Выберите хотя бы один тип!",
        "prepare.scan.nothing_found":"Ничего не найдено.",

        # Prepare step 3 — configs tab
        "prepare.s3.btn_add":        "✅ Добавить выбранное",
        "prepare.s3.btn_all":        "Выбрать все",
        "prepare.s3.btn_none":       "Снять все",
        "prepare.s3.btn_configs":    "Выделить конфиги",
        "prepare.s3.btn_other":      "Выделить другое",
        "prepare.s3.btn_rec":        "⭐ Рекомендуемые",
        "prepare.s3.btn_rec_tip":    "Выделить приложения, которые рекомендуем сохранить",
        "prepare.s3.btn_folder":     "📁 Добавить свою папку",
        "prepare.s3.search_configs": "🔍 Поиск по имени...",
        "prepare.s3.btn_expand":     "↕ Развернуть всё",
        "prepare.s3.btn_collapse":   "↕ Свернуть всё",
        "prepare.s3.status_empty":   "Выбрано: 0",
        "prepare.s3.status":         "Выбрано: {sel} из {total}  •  {sel_size} из {tot_size}",
        "prepare.s3.warn_dup":       "⚠️ Папки есть в Local и Roaming одновременно: {names}",
        "prepare.s3.tab_configs":    "Конфиги ({count})",

        # Prepare step 3 — personal tab
        "prepare.s3.tab_personal":    "Личные файлы ({count})",
        "prepare.s3.btn_add_files":   "📄 Добавить файлы",
        "prepare.s3.btn_add_folder":  "📁 Добавить папку",
        "prepare.s3.search_personal": "🔍 Поиск по имени...",
        "prepare.s3.group_folder":     "📁 По папкам",
        "prepare.s3.group_type":       "🏷 По типу файлов",
        "prepare.s3.group_folder_type":"📁 По папкам + типу",
        "prepare.s3.group_flat":       "📋 Без группировки",
        "prepare.s3.status_zero":     "Выбрано: 0 из {total}",
        "prepare.s3.warn_dup_more":   " и ещё {n}",

        # Prepare step 3 — programs tab
        "prepare.s3.tab_programs":   "Программы ({count})",
        "prepare.s3.prog_col_name":  "Программа",
        "prepare.s3.prog_col_pub":   "Издатель",
        "prepare.s3.prog_col_ver":   "Версия",
        "prepare.s3.prog_col_date":  "Установлена",
        "prepare.s3.prog_all":       "Выбрать все",
        "prepare.s3.prog_none":      "Снять все",
        "prepare.s3.prog_group":     "Группировка:",
        "prepare.s3.prog_grouped":   "📁 По категориям",
        "prepare.s3.prog_flat":      "📋 Без группировки",
        "prepare.s3.prog_search":    "🔍 Поиск по программе или издателю...",
        "prepare.s3.prog_deselect":  "Снять:",
        "prepare.s3.prog_drivers":   "Драйверы",
        "prepare.s3.prog_ms":        "Microsoft",
        "prepare.s3.prog_sys":       "Системные",
        "prepare.s3.prog_hint":      "💡 Драйверы, Microsoft и системные компоненты сняты автоматически — они переустанавливаются сами.",
        "prepare.s3.prog_status":    "Выбрано: {checked} из {total}",
        "prepare.s3.prog_skip_tip":  "⏭ Можно пропустить: переустанавливается автоматически",
        "prepare.s3.prog_rec_tip":   "✅ Рекомендуем включить в список для переустановки",
        "prepare.s3.prog_count":     "{count} программ",

        # Prepare step 4
        "prepare.s4.mode":           "Режим:",
        "prepare.s4.mode_copy":      "Просто скопировать",
        "prepare.s4.mode_archive":   "Архивировать (ZIP)",
        "prepare.s4.btn_create":     "💾 СОЗДАТЬ ФАЙЛ ВОССТАНОВЛЕНИЯ",
        "prepare.s4.tab_configs":    "Конфиги ({count})",
        "prepare.s4.tab_personal":   "Личные файлы ({count})",
        "prepare.s4.summary":        "Итого: {configs} конфигов, {files} файлов{programs}  •  Общий размер: {size}  •  Свободно на {disk}: {free}",
        "prepare.s4.summary_progs":  ", {count} программ",
        "prepare.s4.warn_empty":     "Нет элементов!",
        "prepare.s4.space_title":    "Недостаточно места",
        "prepare.s4.space_msg":      "Нужно: {required}\nДоступно: {free}\n\nОсвободите {diff} или выберите другой диск.",
        "prepare.s4.copy_title":     "Копирование файлов",
        "prepare.s4.done_title":     "Готово",
        "prepare.s4.done_msg":       "✅ Файл восстановления создан!\n\nУспешно: {ok}\n",
        "prepare.s4.done_errors":    "Ошибок: {err}\n",
        "prepare.s4.done_progs":     "Программ в списке: {count}\n",
        "prepare.s4.done_path":      "Путь: {path}",

        # Prepare common
        "prepare.warn_title":     "Внимание",
        "prepare.warn_pick_one":  "Выберите хотя бы один элемент!",
        "prepare.dlg_folder":     "Выберите папку с конфигом",
        "prepare.dlg_folder2":    "Выберите папку",
        "prepare.dlg_files":      "Выберите файлы",

        # Restore
        "restore.btn_back":          "← Назад",
        "restore.title":             "Восстановление",
        "restore.title_session":      "Восстановление — {name}",
        "restore.no_session_name":    "Без названия",
        "restore.no_config":         "Файл конфигурации не найден",
        "restore.no_config_hint":    "Укажите путь к файлу recovery_config.json вручную",
        "restore.btn_pick_config":   "📁 Выбрать файл конфига",
        "restore.dlg_config_title":  "Выберите recovery_config.json",
        "restore.dlg_config_filter": "JSON файлы (*.json);;Все файлы (*.*)",
        "restore.session_info":      "📋 Сессия: {name}  •  Создана: {date}\n🙂 Старый пользователь: {old}  →  Новый: {new}",
        "restore.btn_all":           "Выбрать все",
        "restore.btn_none":          "Снять все",
        "restore.tab_configs":       "Конфиги ({count})",
        "restore.tab_personal":      "Личные файлы ({count})",
        "restore.prog_search":       "🔍 Поиск по программе или издателю...",
        "restore.prog_col_name":     "Программа",
        "restore.prog_col_pub":      "Издатель",
        "restore.prog_col_ver":      "Версия",
        "restore.prog_col_date":     "Установлена",
        "restore.prog_count":        "{count} программ",
        "restore.prog_found":        "Найдено: {count}",
        "restore.prog_total":        "Всего программ: {count}",
        "restore.tab_programs":      "📋 Программы ({count})",
        "restore.btn_restore":       "🔄 ВОССТАНОВИТЬ ВЫБРАННОЕ",
        "restore.warn_title":        "Внимание",
        "restore.warn_pick":         "Выберите элементы!",
        "restore.done_title":        "Завершено",
        "restore.error_title":       "Ошибка",
        "restore.error_load":        "Не удалось загрузить конфиг:\n{error}",
        "restore.progress_title":    "Восстановление",
        "restore.results_prefix":    "Результаты:\n\n",
        "restore.result_ok":         "✅ {name} — успешно\n",
        "restore.result_err":        "❌ {name} — {status}\n",
    },

    "en": {
        # App
        "app.window_title": "WinRecover — Windows Reinstall Assistant",
        "app.btn_logs":     "📋 Logs",
        "app.btn_lang":     "RU",

        # Start screen
        "start.subtitle":         "Windows Reinstall Assistant",
        "start.btn_prepare.title":"🔄  PREPARE FOR REINSTALL",
        "start.btn_prepare.desc": "Save your settings and files before\nreinstalling Windows",
        "start.btn_restore.title":"✅  WINDOWS ALREADY REINSTALLED",
        "start.btn_restore.desc": "Restore files and settings\nfrom your backup",
        "start.btn_rec.title":    "💡  FRESH INSTALL RECOMMENDATIONS",
        "start.btn_rec.desc":     "Useful software after reinstalling Windows:\ntweaks, utilities, developer tools",

        # Log window
        "log.title":     "📋 WinRecover Logs",
        "log.waiting":   "Waiting for new entries...",
        "log.autoscroll":"Auto-scroll",
        "log.clear":     "Clear",
        "log.close":     "Close",
        "log.loaded":    "Loaded {count} lines from file",
        "log.records":   "{count} records",
        "log.cleared":   "Cleared",

        # Recommendations
        "rec.btn_back": "← Back",
        "rec.title":    "💡 Fresh Install Recommendations",
        "rec.hint":     "A curated list of useful programs to install after a fresh Windows installation. "
                        "Click the link next to a program name to open its official page.",

        # Prepare — navigation
        "prepare.btn_back": "← Back",
        "prepare.step1":    "Step 1 of 4 — Disk Analysis",
        "prepare.step2":    "Step 2 of 4 — File Search",
        "prepare.step3":    "Step 3 of 4 — File Selection",
        "prepare.step4":    "Step 4 of 4 — Review & Run",
        "prepare.btn_next": "Next →",

        # Prepare step 1 — disk
        "prepare.system_disk":       "💻 System disk: {disk}\n(Windows will be reinstalled here)",
        "prepare.partitions":         "Detected partitions:",
        "prepare.dest_disk":          "Destination disk:",
        "prepare.dest_folder":        "Folder:",
        "prepare.btn_browse":         "Browse",
        "prepare.session_name":       "Session name:",
        "prepare.dlg_choose_folder":  "Choose folder",
        "prepare.warn_no_other_disk": "⚠️ No other disks found. A 'recover' folder will be created on the system disk.",
        "prepare.warn_no_disk":       "🔴 Connect an external drive to save your data",

        # Prepare step 1 — games warning
        "prepare.games.col_name": "Game Name",
        "prepare.games.col_plat": "Platform",
        "prepare.games.col_size": "Size",
        "prepare.games.tip":      "💡 Move your games to another drive (D:, E:…) before reinstalling — everything on C: will be wiped.",
        "prepare.games.warn":     "⚠️  Found {count} game(s) on {disk}, ~{size} — they will be deleted on reinstall!",
        "prepare.games.show":     "▼ Show list",
        "prepare.games.hide":     "▲ Hide list",

        # Prepare step 1 — vaults warning
        "prepare.vaults.col_name":  "Vault",
        "prepare.vaults.col_path":  "Path",
        "prepare.vaults.col_size":  "Size",
        "prepare.vaults.tip":       "💡 Obsidian stores notes locally. Add vaults via 'Add custom folder' on step 3, or copy them manually.",
        "prepare.vaults.show":      "▼ Show list",
        "prepare.vaults.hide":      "▲ Hide list",
        "prepare.vaults.singular":  "vault",
        "prepare.vaults.few":       "vaults",
        "prepare.vaults.many":      "vaults",
        "prepare.vaults.warn_text": "⚠️  Obsidian: found {count} {plural}{size} on {disk} — notes will be deleted on reinstall!",

        # Prepare step 2 — scan
        "prepare.scan.idle":         "Click the button to search for files on the system disk",
        "prepare.scan.btn":          "🔍 FIND FILES",
        "prepare.scan.running":      "Scanning...",
        "prepare.scan.dlg_title":    "What to search for?",
        "prepare.scan.dlg_header":   "<b style='font-size:16px'>What to search for?</b>",
        "prepare.scan.cb_configs":   "App configs (AppData)\nSettings of installed applications",
        "prepare.scan.cb_personal":  "Personal files\nDocuments, Images, Videos, Music",
        "prepare.scan.cb_programs":  "Installed programs list\nTo know what to reinstall afterwards",
        "prepare.scan.btn_cancel":   "Cancel",
        "prepare.scan.btn_start":    "Start search",
        "prepare.scan.warn_empty":   "Select at least one type!",
        "prepare.scan.nothing_found":"Nothing found.",

        # Prepare step 3 — configs tab
        "prepare.s3.btn_add":        "✅ Add selected",
        "prepare.s3.btn_all":        "Select all",
        "prepare.s3.btn_none":       "Deselect all",
        "prepare.s3.btn_configs":    "Select configs",
        "prepare.s3.btn_other":      "Select other",
        "prepare.s3.btn_rec":        "⭐ Recommended",
        "prepare.s3.btn_rec_tip":    "Select apps recommended to save",
        "prepare.s3.btn_folder":     "📁 Add custom folder",
        "prepare.s3.search_configs": "🔍 Search by name...",
        "prepare.s3.btn_expand":     "↕ Expand all",
        "prepare.s3.btn_collapse":   "↕ Collapse all",
        "prepare.s3.status_empty":   "Selected: 0",
        "prepare.s3.status":         "Selected: {sel} of {total}  •  {sel_size} of {tot_size}",
        "prepare.s3.warn_dup":       "⚠️ Folders exist in both Local and Roaming: {names}",
        "prepare.s3.tab_configs":    "Configs ({count})",

        # Prepare step 3 — personal tab
        "prepare.s3.tab_personal":    "Personal files ({count})",
        "prepare.s3.btn_add_files":   "📄 Add files",
        "prepare.s3.btn_add_folder":  "📁 Add folder",
        "prepare.s3.search_personal": "🔍 Search by name...",
        "prepare.s3.group_folder":     "📁 By folders",
        "prepare.s3.group_type":       "🏷 By file type",
        "prepare.s3.group_folder_type":"📁 By folders + type",
        "prepare.s3.group_flat":       "📋 No grouping",
        "prepare.s3.status_zero":     "Selected: 0 of {total}",
        "prepare.s3.warn_dup_more":   " and {n} more",

        # Prepare step 3 — programs tab
        "prepare.s3.tab_programs":   "Programs ({count})",
        "prepare.s3.prog_col_name":  "Program",
        "prepare.s3.prog_col_pub":   "Publisher",
        "prepare.s3.prog_col_ver":   "Version",
        "prepare.s3.prog_col_date":  "Installed",
        "prepare.s3.prog_all":       "Select all",
        "prepare.s3.prog_none":      "Deselect all",
        "prepare.s3.prog_group":     "Group by:",
        "prepare.s3.prog_grouped":   "📁 By category",
        "prepare.s3.prog_flat":      "📋 No grouping",
        "prepare.s3.prog_search":    "🔍 Search by program or publisher...",
        "prepare.s3.prog_deselect":  "Deselect:",
        "prepare.s3.prog_drivers":   "Drivers",
        "prepare.s3.prog_ms":        "Microsoft",
        "prepare.s3.prog_sys":       "System",
        "prepare.s3.prog_hint":      "💡 Drivers, Microsoft and system components are auto-deselected — they reinstall automatically.",
        "prepare.s3.prog_status":    "Selected: {checked} of {total}",
        "prepare.s3.prog_skip_tip":  "⏭ Skip: reinstalls automatically",
        "prepare.s3.prog_rec_tip":   "✅ Recommended to include in reinstall list",
        "prepare.s3.prog_count":     "{count} programs",

        # Prepare step 4
        "prepare.s4.mode":           "Mode:",
        "prepare.s4.mode_copy":      "Copy files",
        "prepare.s4.mode_archive":   "Archive (ZIP)",
        "prepare.s4.btn_create":     "💾 CREATE RECOVERY FILE",
        "prepare.s4.tab_configs":    "Configs ({count})",
        "prepare.s4.tab_personal":   "Personal files ({count})",
        "prepare.s4.summary":        "Total: {configs} configs, {files} files{programs}  •  Size: {size}  •  Free on {disk}: {free}",
        "prepare.s4.summary_progs":  ", {count} programs",
        "prepare.s4.warn_empty":     "No items selected!",
        "prepare.s4.space_title":    "Not enough space",
        "prepare.s4.space_msg":      "Required: {required}\nAvailable: {free}\n\nFree up {diff} or choose another disk.",
        "prepare.s4.copy_title":     "Copying files",
        "prepare.s4.done_title":     "Done",
        "prepare.s4.done_msg":       "✅ Recovery file created!\n\nSucceeded: {ok}\n",
        "prepare.s4.done_errors":    "Errors: {err}\n",
        "prepare.s4.done_progs":     "Programs in list: {count}\n",
        "prepare.s4.done_path":      "Path: {path}",

        # Prepare common
        "prepare.warn_title":     "Warning",
        "prepare.warn_pick_one":  "Select at least one item!",
        "prepare.dlg_folder":     "Choose config folder",
        "prepare.dlg_folder2":    "Choose folder",
        "prepare.dlg_files":      "Choose files",

        # Restore
        "restore.btn_back":          "← Back",
        "restore.title":             "Restore",
        "restore.title_session":      "Restore — {name}",
        "restore.no_session_name":    "Untitled",
        "restore.no_config":         "Configuration file not found",
        "restore.no_config_hint":    "Specify the path to recovery_config.json manually",
        "restore.btn_pick_config":   "📁 Choose config file",
        "restore.dlg_config_title":  "Choose recovery_config.json",
        "restore.dlg_config_filter": "JSON files (*.json);;All files (*.*)",
        "restore.session_info":      "📋 Session: {name}  •  Created: {date}\n🙂 Original user: {old}  →  Current: {new}",
        "restore.btn_all":           "Select all",
        "restore.btn_none":          "Deselect all",
        "restore.tab_configs":       "Configs ({count})",
        "restore.tab_personal":      "Personal files ({count})",
        "restore.prog_search":       "🔍 Search by program or publisher...",
        "restore.prog_col_name":     "Program",
        "restore.prog_col_pub":      "Publisher",
        "restore.prog_col_ver":      "Version",
        "restore.prog_col_date":     "Installed",
        "restore.prog_count":        "{count} programs",
        "restore.prog_found":        "Found: {count}",
        "restore.prog_total":        "Total programs: {count}",
        "restore.tab_programs":      "📋 Programs ({count})",
        "restore.btn_restore":       "🔄 RESTORE SELECTED",
        "restore.warn_title":        "Warning",
        "restore.warn_pick":         "Select items to restore!",
        "restore.done_title":        "Done",
        "restore.error_title":       "Error",
        "restore.error_load":        "Failed to load config:\n{error}",
        "restore.progress_title":    "Restore",
        "restore.results_prefix":    "Results:\n\n",
        "restore.result_ok":         "✅ {name} — done\n",
        "restore.result_err":        "❌ {name} — {status}\n",
    },
}

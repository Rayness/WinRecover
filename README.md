# WinRecover

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](../../releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?logo=windows)](../../releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Lang](https://img.shields.io/badge/lang-RU%20%7C%20EN-orange)](#)

**Помощник при переустановке Windows** — инструмент, который помогает сохранить конфиги, личные файлы и список программ перед чистой установкой, а после — восстановить всё обратно.

> [English version →](README_EN.md)

![Скриншот](assets/screenshoot.png)

---

## Возможности

### Подготовка к переустановке
- **Сканирование AppData** — находит конфиги установленных программ (VS Code, Discord, OBS, JetBrains, а также ИИ-агенты и инструменты: Claude Desktop/Code, Cursor, Windsurf, Ollama, LM Studio и др.) с рекомендациями что важно сохранить, а что восстановится само
- **SSH-ключи** — автоматически находит `~/.ssh/` и предлагает включить в резервную копию
- **Личные файлы** — Documents, Pictures, Videos, Music, Downloads
- **Список программ** — сканирует реестр Windows, группирует по категориям (включая «🤖 ИИ-инструменты»), генерирует Markdown-файл для восстановления
- **Предупреждение об играх** — определяет игры на диске C: из Steam, Epic Games и GOG Galaxy
- **Предупреждение об Obsidian** — находит локальные хранилища заметок
- **Прогресс сканирования** — отображается в процентах по фазам
- **Создание резервной копии** — копирует или архивирует (ZIP) выбранные файлы на другой диск

### Восстановление после переустановки
- Просмотр резервной копии с деревом файлов
- Список установленных программ для ручной переустановки
- Восстановление файлов из резервной копии (из копии или ZIP-архива)

### Рекомендации при чистой установке
- Curated-список полезного ПО по категориям: твики, кастомизация, разработка, **ИИ-агенты и инструменты**, безопасность, медиа и др.
- Поиск по названию и описанию
- Ссылки на официальные страницы каждого инструмента

---

## Структура резервной копии

Копия повторяет структуру вашей папки пользователя — так данные можно
восстановить вручную, даже если приложение не запустится:

```
recover/
├── КАК_ВОССТАНОВИТЬ.txt        # Инструкция (RU/EN) и карта «что → куда»
├── recovery_config.json        # Метаданные сессии (читает экран восстановления)
├── programs_list.md            # Список программ для переустановки
├── configs/                    # Зеркало конфигов относительно %USERPROFILE%
│   ├── AppData/Roaming/Code/…  → %USERPROFILE%\AppData\Roaming\Code
│   └── .ssh/id_rsa             → %USERPROFILE%\.ssh\id_rsa
└── personal/                   # Зеркало личных файлов
    └── Documents/cv.pdf        → %USERPROFILE%\Documents\cv.pdf
```

В режиме архива те же папки `configs/` и `personal/` лежат внутри
`recovery_archive.zip`. **Ручное восстановление:** распакуйте архив (если был)
и скопируйте содержимое `configs\` и `personal\` обратно в `C:\Users\<имя>\`.

---

## Скачать

> Готовый `.exe` не требует установки — скачайте на странице [Releases](../../releases/latest) и запустите.

---

## Запуск из исходников

### Требования
- Windows 10 / 11
- Python 3.11+

### Установка

```bash
git clone https://github.com/YOUR_USERNAME/WinRecover.git
cd WinRecover
pip install -r requirements.txt
python main.py
```

### Зависимости

| Пакет | Назначение |
|-------|-----------|
| `PySide6` | GUI (Qt6) |
| `psutil` | Информация о дисках и разделах |

> Архивы создаются в формате ZIP стандартным модулем `zipfile` — отдельная зависимость не нужна.

---

## Структура проекта

```
WinRecover/
├── main.py                    # Точка входа
├── config_manager.py          # Управление конфигом резервной копии
├── test_file_operations.py    # Тесты copy/archive → restore (python test_file_operations.py)
├── requirements.txt
├── assets/                    # Иконка и скриншоты
├── core/
│   ├── system_detector.py     # Автодетект состояния (до/после переустановки)
│   ├── file_scanner.py        # Сканирование AppData, личных файлов, SSH
│   ├── games_scanner.py       # Сканирование игр (Steam, Epic, GOG) и Obsidian
│   └── programs_scanner.py    # Сканирование установленных программ через реестр
├── ui/
│   ├── app.py                 # Главное окно, навигация между экранами
│   ├── style.py               # Тёмная тема (QSS)
│   ├── start_screen.py        # Стартовый экран
│   ├── prepare_screen.py      # Экран подготовки (шаги 1–4)
│   ├── restore_screen.py      # Экран восстановления
│   ├── recommendations_screen.py  # Рекомендации по ПО
│   └── components/
│       ├── file_list.py       # Кастомный QTreeWidget с чекбоксами
│       ├── disk_info.py       # Виджет информации о диске
│       └── progress_modal.py  # Модальное окно прогресса
└── utils/
    ├── helpers.py             # Вспомогательные функции
    └── i18n.py                # Локализация (RU / EN)
```

---

## Лицензия

[MIT](LICENSE)

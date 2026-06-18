# WinRecover

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](../../releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?logo=windows)](../../releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Lang](https://img.shields.io/badge/lang-RU%20%7C%20EN-orange)](#)

**Windows Reinstall Assistant** — a tool that helps you back up configs, personal files, and the list of installed programs before a clean Windows install, and restore everything afterward.

> [Русская версия →](README.md)

![Screenshot](assets/screenshoot.png)

---

## Features

### Before Reinstalling
- **AppData Scanning** — finds configs of installed programs (VS Code, Discord, OBS, JetBrains, plus AI agents & tools: Claude Desktop/Code, Cursor, Windsurf, Ollama, LM Studio, etc.) with recommendations on what's worth keeping vs. what restores automatically
- **SSH Keys** — automatically locates `~/.ssh/` and offers to include it in the backup
- **Personal Files** — Documents, Pictures, Videos, Music, Downloads
- **Program List** — scans the Windows registry, groups by category (including "🤖 AI Tools"), generates a Markdown file for easy reinstallation
- **Games Warning** — detects games on drive C: from Steam, Epic Games, and GOG Galaxy
- **Obsidian Warning** — finds local Obsidian vaults
- **Scan Progress** — shown as a percentage across phases
- **Backup Creation** — copies or archives (ZIP) selected files to another drive

### After Reinstalling
- Browse the backup with a file tree view
- Installed programs list for manual reinstallation
- Restore files from the backup (from a copy or a ZIP archive)

### Fresh Install Recommendations
- Curated list of useful software by category: tweaks, customization, development, **AI agents & tools**, security, media, and more
- Search by name and description
- Links to the official page of each tool

---

## Backup Layout

The backup mirrors your user folder, so you can restore data manually even if
the app won't start:

```
recover/
├── КАК_ВОССТАНОВИТЬ.txt        # Restore guide (RU/EN) with a "what → where" map
├── recovery_config.json        # Session metadata (read by the restore screen)
├── programs_list.md            # Program list for reinstallation
├── configs/                    # Mirror of configs relative to %USERPROFILE%
│   ├── AppData/Roaming/Code/…  → %USERPROFILE%\AppData\Roaming\Code
│   └── .ssh/id_rsa             → %USERPROFILE%\.ssh\id_rsa
└── personal/                   # Mirror of personal files
    └── Documents/cv.pdf        → %USERPROFILE%\Documents\cv.pdf
```

In archive mode the same `configs/` and `personal/` folders live inside
`recovery_archive.zip`. **Manual restore:** extract the archive (if any) and
copy the contents of `configs\` and `personal\` back into `C:\Users\<you>\`.

---

## Download

> The `.exe` requires no installation — download it from [Releases](../../releases/latest) and run.

---

## Run from Source

### Requirements
- Windows 10 / 11
- Python 3.11+

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/WinRecover.git
cd WinRecover
pip install -r requirements.txt
python main.py
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `PySide6` | GUI (Qt6) |
| `psutil` | Disk and partition info |

> Archives are created in ZIP format via the standard `zipfile` module — no extra dependency needed.

---

## Project Structure

```
WinRecover/
├── main.py                    # Entry point
├── config_manager.py          # Backup config management
├── test_file_operations.py    # copy/archive → restore tests (python test_file_operations.py)
├── requirements.txt
├── assets/                    # Icon and screenshots
├── core/
│   ├── system_detector.py     # Auto-detect state (before/after reinstall)
│   ├── file_scanner.py        # AppData, personal files, SSH scanning
│   ├── games_scanner.py       # Game scanning (Steam, Epic, GOG) and Obsidian
│   └── programs_scanner.py    # Installed programs via Windows registry
├── ui/
│   ├── app.py                 # Main window, screen navigation
│   ├── style.py               # Dark theme (QSS)
│   ├── start_screen.py        # Start screen
│   ├── prepare_screen.py      # Preparation screen (steps 1–4)
│   ├── restore_screen.py      # Restore screen
│   ├── recommendations_screen.py  # Software recommendations
│   └── components/
│       ├── file_list.py       # Custom QTreeWidget with checkboxes
│       ├── disk_info.py       # Disk info widget
│       └── progress_modal.py  # Modal progress dialog
└── utils/
    ├── helpers.py             # Utility functions
    └── i18n.py                # Localization (RU / EN)
```

---

## License

[MIT](LICENSE)

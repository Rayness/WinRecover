"""Менеджер конфигурации recovery_config.json."""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "recovery_config.json"


def create_default_config(
    destination_folder: str,
    system_disk: str,
    system_disk_total: int,
    system_disk_free: int,
    old_username: str,
    session_name: str | None = None,
    archive_mode: bool = False,
) -> dict[str, Any]:
    """Создаёт структуру конфига по умолчанию."""
    if session_name is None:
        session_name = f"Восстановление {datetime.now().strftime('%d.%m.%Y')}"
    return {
        "session_name": session_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "system_disk": system_disk,
        "system_disk_total_bytes": system_disk_total,
        "system_disk_free_before": system_disk_free,
        "destination_folder": destination_folder,
        "archive_mode": archive_mode,
        "old_username": old_username,
        "entries": [],
    }


def add_entry(
    config: dict,
    entry_type: str,
    name: str,
    source_path: str,
    relative_path: str,
    is_dir: bool,
    size_bytes: int,
) -> dict:
    """Добавляет запись в конфиг."""
    entry = {
        "type": entry_type,
        "name": name,
        "source_path": source_path,
        "relative_path": relative_path,
        "is_dir": is_dir,
        "size_bytes": size_bytes,
        "status": None,
    }
    config["entries"].append(entry)
    return entry


def save_config(config: dict, folder: Path) -> Path:
    """Атомарно сохраняет конфиг в указанную папку."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / CONFIG_FILENAME
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(folder), suffix=".tmp", prefix="recovery_config_"
        )
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        tmp = Path(tmp_path)
        tmp.replace(target)
        logger.info("Конфиг сохранён: %s", target)
    except Exception:
        logger.exception("Ошибка сохранения конфига")
        raise
    return target


def load_config(config_path: Path) -> dict[str, Any]:
    """Загружает конфиг из файла."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

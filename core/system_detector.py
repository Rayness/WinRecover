"""Определение состояния системы и поиск конфигов."""

import logging
import time
from pathlib import Path

import psutil

from config_manager import CONFIG_FILENAME, load_config
from core.disk_analyzer import get_all_partitions

logger = logging.getLogger(__name__)


def find_recovery_configs() -> list[Path]:
    """Ищет recovery_config.json на всех дисках (корень + 1 уровень вложенности)."""
    logger.info("=" * 60)
    logger.info("[find_configs] НАЧАЛО поиска recovery_config.json на всех дисках")
    configs = []
    start = time.time()

    for part in psutil.disk_partitions(all=False):
        root = Path(part.mountpoint)
        logger.info("[find_configs] Проверяю диск: %s", root)
        try:
            # Проверяем корень
            config_file = root / CONFIG_FILENAME
            logger.debug("[find_configs]   Проверяю: %s", config_file)
            if config_file.is_file():
                logger.info("[find_configs]   НАЙДЕН в корне: %s", config_file)
                configs.append(config_file)

            # Проверяем папки первого уровня
            dir_count = 0
            for entry in root.iterdir():
                if entry.is_dir():
                    dir_count += 1
                    config_file = entry / CONFIG_FILENAME
                    if config_file.is_file():
                        logger.info("[find_configs]   НАЙДЕН: %s", config_file)
                        configs.append(config_file)
            logger.info("[find_configs]   Проверено %d папок на %s", dir_count, root)

        except (PermissionError, OSError) as e:
            logger.warning("[find_configs]   Ошибка доступа к %s: %s", root, e)
            continue

    elapsed = time.time() - start
    logger.info("[find_configs] ЗАВЕРШЕНО: найдено %d конфигов за %.2fс", len(configs), elapsed)
    logger.info("=" * 60)
    return configs


def detect_reinstall(config_path: Path) -> bool:
    """
    Определяет, была ли переустановлена Windows.
    Возвращает True если свободное место на системном диске
    увеличилось на 80%+ по сравнению с сохранённым значением.
    """
    logger.info("[detect_reinstall] Проверяю конфиг: %s", config_path)
    try:
        config = load_config(config_path)
        system_disk = config.get("system_disk", "C:\\")
        saved_free = config.get("system_disk_free_before", 0)

        if saved_free == 0:
            logger.info("[detect_reinstall] saved_free=0, пропускаю")
            return False

        usage = psutil.disk_usage(system_disk)
        current_free = usage.free

        increase = (current_free - saved_free) / saved_free
        logger.info(
            "[detect_reinstall] диск=%s, было_свободно=%d, сейчас=%d, рост=%.1f%%",
            system_disk, saved_free, current_free, increase * 100,
        )
        return increase >= 0.8

    except Exception:
        logger.exception("[detect_reinstall] Ошибка проверки")
        return False


def check_startup_state() -> tuple[str, Path | None]:
    """
    Определяет состояние при запуске.
    Возвращает:
      ("start", None) — показать стартовый экран
      ("restore", config_path) — показать экран восстановления
    """
    logger.info("[check_startup] Определяю состояние при запуске...")
    configs = find_recovery_configs()
    for config_path in configs:
        if detect_reinstall(config_path):
            logger.info("[check_startup] -> ВОССТАНОВЛЕНИЕ (переустановка обнаружена)")
            return "restore", config_path
    result = ("start", configs[0] if configs else None)
    logger.info("[check_startup] -> СТАРТ (конфигов: %d)", len(configs))
    return result

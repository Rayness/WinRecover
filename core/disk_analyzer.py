"""Анализ дисков и разделов."""

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


@dataclass
class DiskPartition:
    """Информация о разделе диска."""
    device: str
    mountpoint: str
    label: str
    fstype: str
    total: int
    used: int
    free: int

    @property
    def usage_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.used / self.total) * 100


def get_all_partitions() -> list[DiskPartition]:
    """Возвращает список всех разделов дисков."""
    logger.info("[get_all_partitions] Получаю список разделов...")
    start = time.time()
    partitions = []
    for part in psutil.disk_partitions(all=False):
        logger.info("[get_all_partitions] Раздел: %s (%s, %s)", part.device, part.mountpoint, part.fstype)
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError) as e:
            logger.warning("[get_all_partitions] Не удалось получить информацию: %s — %s", part.mountpoint, e)
            continue

        label = _get_volume_label(part.mountpoint)
        p = DiskPartition(
            device=part.device,
            mountpoint=part.mountpoint,
            label=label,
            fstype=part.fstype,
            total=usage.total,
            used=usage.used,
            free=usage.free,
        )
        partitions.append(p)
        logger.info("[get_all_partitions]   -> label='%s', total=%d, free=%d, used=%.0f%%",
                    label, usage.total, usage.free, p.usage_percent)

    elapsed = time.time() - start
    logger.info("[get_all_partitions] Найдено %d разделов за %.2fс", len(partitions), elapsed)
    return partitions


def _get_volume_label(mountpoint: str) -> str:
    """Получает метку тома (Windows)."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_unicode_buffer(1024)
        kernel32.GetVolumeInformationW(
            mountpoint, buf, 1024, None, None, None, None, 0
        )
        return buf.value or ""
    except Exception as e:
        logger.debug("[_get_volume_label] Ошибка для %s: %s", mountpoint, e)
        return ""


def get_system_disk() -> str:
    """Возвращает букву системного диска (например 'C:\\')."""
    win_dir = os.environ.get("SystemRoot", r"C:\Windows")
    result = str(Path(win_dir).anchor)
    logger.info("[get_system_disk] Системный диск: %s (из %s)", result, win_dir)
    return result


def find_best_destination(partitions: list[DiskPartition], system_disk: str) -> DiskPartition | None:
    """Находит раздел с наибольшим свободным местом (кроме системного)."""
    non_system = [p for p in partitions if p.mountpoint.upper() != system_disk.upper()]
    if non_system:
        best = max(non_system, key=lambda p: p.free)
        logger.info("[find_best_destination] Лучший диск: %s (свободно: %d)", best.mountpoint, best.free)
        return best
    logger.warning("[find_best_destination] Нет дисков кроме системного")
    return None

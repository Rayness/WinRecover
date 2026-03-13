"""Копирование, архивация, восстановление файлов."""

import logging
import shutil
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class CopyProgress:
    """Прогресс копирования."""
    current_file: str = ""
    copied_bytes: int = 0
    total_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: float = 0.0

    @property
    def percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return min(100.0, (self.copied_bytes / self.total_bytes) * 100)


def _collect_files(source: Path) -> list[tuple[Path, int]]:
    """Собирает список файлов с размерами."""
    files = []
    if source.is_file():
        try:
            files.append((source, source.stat().st_size))
        except OSError:
            pass
    elif source.is_dir():
        try:
            for f in source.rglob("*"):
                if f.is_file():
                    try:
                        files.append((f, f.stat().st_size))
                    except OSError:
                        pass
        except OSError:
            pass
    return files


def copy_entries(
    entries: list[dict],
    destination: Path,
    archive_mode: bool,
    progress_callback: Callable[[CopyProgress], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[dict]:
    """
    Копирует/архивирует записи в папку назначения.
    Возвращает обновлённый список entries со статусами.
    """
    logger.info("=" * 60)
    logger.info("[copy_entries] НАЧАЛО копирования: %d записей, режим=%s, путь=%s",
                len(entries), "архив" if archive_mode else "копия", destination)
    total_bytes = sum(e.get("size_bytes", 0) for e in entries)
    logger.info("[copy_entries] Общий размер: %d байт", total_bytes)
    progress = CopyProgress(total_bytes=total_bytes)
    start_time = time.time()

    if archive_mode:
        result = _copy_as_archive(entries, destination, progress, progress_callback, cancel_check, start_time)
    else:
        result = _copy_flat(entries, destination, progress, progress_callback, cancel_check, start_time)

    elapsed = time.time() - start_time
    ok = sum(1 for e in result if e.get("status") == "ok")
    err = sum(1 for e in result if e.get("status", "").startswith("error"))
    logger.info("[copy_entries] ЗАВЕРШЕНО за %.1fс: ok=%d, ошибок=%d", elapsed, ok, err)
    logger.info("=" * 60)
    return result


def _update_speed(progress: CopyProgress, start_time: float):
    """Обновляет скорость и ETA."""
    elapsed = time.time() - start_time
    if elapsed > 0:
        progress.speed_bps = progress.copied_bytes / elapsed
        remaining = progress.total_bytes - progress.copied_bytes
        if progress.speed_bps > 0:
            progress.eta_seconds = remaining / progress.speed_bps
        else:
            progress.eta_seconds = 0


def _copy_flat(
    entries: list[dict],
    destination: Path,
    progress: CopyProgress,
    progress_callback: Callable | None,
    cancel_check: Callable | None,
    start_time: float,
) -> list[dict]:
    """Копирует файлы в обычном режиме."""
    for i, entry in enumerate(entries):
        if cancel_check and cancel_check():
            logger.info("[copy_flat] ОТМЕНА на записи %d/%d", i + 1, len(entries))
            break

        source = Path(entry["source_path"])
        entry_type = entry.get("type", "config")

        if entry_type == "config":
            dest_dir = destination / "configs" / entry["name"]
        else:
            dest_dir = destination / "personal"

        logger.info("[copy_flat] [%d/%d] Копирую: %s -> %s", i + 1, len(entries), entry["name"], dest_dir)
        entry_start = time.time()

        try:
            progress.current_file = entry["name"]
            if progress_callback:
                progress_callback(progress)

            if source.is_dir():
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(
                    source, dest_dir,
                    dirs_exist_ok=True,
                    ignore_dangling_symlinks=True,
                )
            elif source.is_file():
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest_dir / source.name)

            entry["status"] = "ok"
            entry_elapsed = time.time() - entry_start
            logger.info("[copy_flat]   -> OK за %.2fс (%d байт)", entry_elapsed, entry.get("size_bytes", 0))

        except Exception as e:
            entry["status"] = f"error: {e}"
            logger.error("[copy_flat]   -> ОШИБКА: %s", e)

        progress.copied_bytes += entry.get("size_bytes", 0)
        _update_speed(progress, start_time)
        if progress_callback:
            progress_callback(progress)

    return entries


def _copy_as_archive(
    entries: list[dict],
    destination: Path,
    progress: CopyProgress,
    progress_callback: Callable | None,
    cancel_check: Callable | None,
    start_time: float,
) -> list[dict]:
    """Копирует файлы в ZIP-архив."""
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "recovery_archive.zip"
    logger.info("[copy_archive] Создаю архив: %s", archive_path)

    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, entry in enumerate(entries):
                if cancel_check and cancel_check():
                    logger.info("[copy_archive] ОТМЕНА на записи %d/%d", i + 1, len(entries))
                    break

                source = Path(entry["source_path"])
                entry_type = entry.get("type", "config")
                prefix = "configs" if entry_type == "config" else "personal"

                logger.info("[copy_archive] [%d/%d] Добавляю: %s", i + 1, len(entries), entry["name"])
                entry_start = time.time()

                try:
                    progress.current_file = entry["name"]
                    if progress_callback:
                        progress_callback(progress)

                    if source.is_dir():
                        file_count = 0
                        for file_path in source.rglob("*"):
                            if file_path.is_file():
                                arcname = f"{prefix}/{entry['name']}/{file_path.relative_to(source)}"
                                zf.write(file_path, arcname)
                                file_count += 1
                        logger.info("[copy_archive]   -> %d файлов добавлено", file_count)
                    elif source.is_file():
                        arcname = f"{prefix}/{source.name}"
                        zf.write(source, arcname)

                    entry["status"] = "ok"
                    entry_elapsed = time.time() - entry_start
                    logger.info("[copy_archive]   -> OK за %.2fс", entry_elapsed)

                except Exception as e:
                    entry["status"] = f"error: {e}"
                    logger.error("[copy_archive]   -> ОШИБКА: %s", e)

                progress.copied_bytes += entry.get("size_bytes", 0)
                _update_speed(progress, start_time)
                if progress_callback:
                    progress_callback(progress)

    except Exception as e:
        logger.exception("[copy_archive] КРИТИЧЕСКАЯ ОШИБКА создания архива")
        for entry in entries:
            if entry["status"] is None:
                entry["status"] = f"error: {e}"

    return entries


def restore_entries(
    entries: list[dict],
    source_folder: Path,
    old_username: str,
    new_username: str,
    archive_mode: bool,
    progress_callback: Callable[[CopyProgress], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[dict]:
    """Восстанавливает файлы из резервной копии."""
    logger.info("=" * 60)
    logger.info("[restore] НАЧАЛО восстановления: %d записей из %s", len(entries), source_folder)
    logger.info("[restore] Замена пользователя: '%s' -> '%s'", old_username, new_username)
    total_bytes = sum(e.get("size_bytes", 0) for e in entries)
    progress = CopyProgress(total_bytes=total_bytes)
    start_time = time.time()

    if archive_mode:
        logger.info("[restore] Распаковка архива...")
        _extract_archive(source_folder)

    user_dir = Path.home()
    logger.info("[restore] Домашняя папка: %s", user_dir)

    for i, entry in enumerate(entries):
        if cancel_check and cancel_check():
            logger.info("[restore] ОТМЕНА на записи %d/%d", i + 1, len(entries))
            break

        try:
            progress.current_file = entry["name"]
            if progress_callback:
                progress_callback(progress)

            entry_type = entry.get("type", "config")
            if entry_type == "config":
                src = source_folder / "configs" / entry["name"]
            else:
                src = source_folder / "personal" / entry["name"]

            rel_path = entry.get("relative_path", "")
            rel_path = rel_path.replace(old_username, new_username)
            dest = user_dir / rel_path

            logger.info("[restore] [%d/%d] %s: %s -> %s", i + 1, len(entries), entry["name"], src, dest)

            if src.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dest, dirs_exist_ok=True)
            elif src.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

            entry["status"] = "ok"
            logger.info("[restore]   -> OK")

        except Exception as e:
            entry["status"] = f"error: {e}"
            logger.error("[restore]   -> ОШИБКА: %s", e)

        progress.copied_bytes += entry.get("size_bytes", 0)
        _update_speed(progress, start_time)
        if progress_callback:
            progress_callback(progress)

    elapsed = time.time() - start_time
    ok = sum(1 for e in entries if e.get("status") == "ok")
    err = sum(1 for e in entries if e.get("status", "").startswith("error"))
    logger.info("[restore] ЗАВЕРШЕНО за %.1fс: ok=%d, ошибок=%d", elapsed, ok, err)
    logger.info("=" * 60)
    return entries


def _extract_archive(source_folder: Path):
    """Распаковывает архив в папку."""
    archive_path = source_folder / "recovery_archive.zip"
    if archive_path.exists():
        logger.info("[extract] Распаковываю: %s", archive_path)
        start = time.time()
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(source_folder)
        elapsed = time.time() - start
        logger.info("[extract] Архив распакован за %.1fс", elapsed)
    else:
        logger.warning("[extract] Архив не найден: %s", archive_path)

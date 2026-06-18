"""Roundtrip-тесты copy/archive → restore.

Структура копии зеркалит папку пользователя (configs/<rel>, personal/<rel>),
поэтому восстановление работает, и пользователь может восстановить вручную.

Запуск: python test_file_operations.py
"""

import tempfile
from pathlib import Path

import core.file_operations as fo
from core.file_operations import copy_entries, restore_entries, MANIFEST_FILENAME


def _restore_into(entries, backup, new_home, archive):
    new_home.mkdir(parents=True, exist_ok=True)
    orig = fo.Path.home
    fo.Path.home = staticmethod(lambda: new_home)
    try:
        restore_entries([dict(e) for e in entries], backup,
                        "olduser", "newuser", archive_mode=archive)
    finally:
        fo.Path.home = orig


def test_personal_dir_roundtrip():
    for archive in (False, True):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src_dir = tmp / "home" / "MyNotes"
            src_dir.mkdir(parents=True)
            (src_dir / "note.txt").write_text("hello", encoding="utf-8")

            entry = {"type": "personal", "name": "MyNotes",
                     "source_path": str(src_dir), "relative_path": "MyNotes",
                     "is_dir": True, "size_bytes": 5, "status": None}
            backup = tmp / "backup"
            copy_entries([dict(entry)], backup, archive_mode=archive)
            if not archive:
                assert (backup / "personal" / "MyNotes" / "note.txt").is_file()

            _restore_into([entry], backup, tmp / "new_home", archive)
            r = tmp / "new_home" / "MyNotes" / "note.txt"
            assert r.read_text(encoding="utf-8") == "hello", f"archive={archive}"


def test_config_mirrors_user_folder():
    """Конфиг хранится по реальному относительному пути — структура
    самодокументируема (configs/AppData/Roaming/Code, configs/.ssh/id_rsa)."""
    for archive in (False, True):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            home = tmp / "home"
            ssh = home / ".ssh"
            ssh.mkdir(parents=True)
            (ssh / "id_rsa").write_text("KEY", encoding="utf-8")
            code = home / "AppData" / "Roaming" / "Code"
            code.mkdir(parents=True)
            (code / "settings.json").write_text("{}", encoding="utf-8")

            entries = [
                {"type": "config", "name": "id_rsa", "source_path": str(ssh / "id_rsa"),
                 "relative_path": ".ssh/id_rsa", "is_dir": False, "size_bytes": 3, "status": None},
                {"type": "config", "name": "Code", "source_path": str(code),
                 "relative_path": "AppData/Roaming/Code", "is_dir": True, "size_bytes": 2, "status": None},
            ]
            backup = tmp / "backup"
            copy_entries([dict(e) for e in entries], backup, archive_mode=archive)
            if not archive:
                assert (backup / "configs" / ".ssh" / "id_rsa").is_file(), "ключ не зеркалит путь"
                assert (backup / "configs" / "AppData" / "Roaming" / "Code" / "settings.json").is_file()

            _restore_into(entries, backup, tmp / "new_home", archive)
            assert (tmp / "new_home" / ".ssh" / "id_rsa").read_text(encoding="utf-8") == "KEY", f"archive={archive}"
            assert (tmp / "new_home" / "AppData" / "Roaming" / "Code" / "settings.json").is_file(), f"archive={archive}"


def test_personal_name_collision():
    """Два файла с одинаковым именем из разных папок не перезаписывают друг друга (B5)."""
    for archive in (False, True):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            home = tmp / "home"
            (home / "Documents").mkdir(parents=True)
            (home / "Downloads").mkdir(parents=True)
            (home / "Documents" / "report.pdf").write_text("DOC", encoding="utf-8")
            (home / "Downloads" / "report.pdf").write_text("DL", encoding="utf-8")

            entries = [
                {"type": "personal", "name": "report.pdf",
                 "source_path": str(home / "Documents" / "report.pdf"),
                 "relative_path": "Documents/report.pdf", "is_dir": False, "size_bytes": 3, "status": None},
                {"type": "personal", "name": "report.pdf",
                 "source_path": str(home / "Downloads" / "report.pdf"),
                 "relative_path": "Downloads/report.pdf", "is_dir": False, "size_bytes": 2, "status": None},
            ]
            backup = tmp / "backup"
            copy_entries([dict(e) for e in entries], backup, archive_mode=archive)
            _restore_into(entries, backup, tmp / "new_home", archive)

            assert (tmp / "new_home" / "Documents" / "report.pdf").read_text(encoding="utf-8") == "DOC", f"archive={archive}"
            assert (tmp / "new_home" / "Downloads" / "report.pdf").read_text(encoding="utf-8") == "DL", f"archive={archive}"


def test_manifest_written():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        f = tmp / "home" / "Documents" / "a.txt"
        f.parent.mkdir(parents=True)
        f.write_text("x", encoding="utf-8")
        entry = {"type": "personal", "name": "a.txt", "source_path": str(f),
                 "relative_path": "Documents/a.txt", "is_dir": False, "size_bytes": 1, "status": None}
        backup = tmp / "backup"
        copy_entries([dict(entry)], backup, archive_mode=False)
        manifest = backup / MANIFEST_FILENAME
        assert manifest.is_file(), "инструкция не создана"
        text = manifest.read_text(encoding="utf-8")
        assert "personal\\Documents\\a.txt" in text
        assert "%USERPROFILE%\\Documents/a.txt" in text or "%USERPROFILE%\\Documents\\a.txt" in text


if __name__ == "__main__":
    test_personal_dir_roundtrip()
    test_config_mirrors_user_folder()
    test_personal_name_collision()
    test_manifest_written()
    print("OK: copy+archive→restore, зеркальная структура, коллизии, инструкция")

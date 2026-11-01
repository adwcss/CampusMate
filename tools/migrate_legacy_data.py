"""Explicit non-destructive migration of the received single-school SQLite data."""
import argparse
import os
from pathlib import Path
import sqlite3
import tempfile
from contextlib import closing


def migrate(source, destination):
    source = Path(source).resolve(strict=True)
    target = Path(destination).resolve() / "schools" / "hnvust" / "guide.sqlite3"
    if not source.is_file() or source == target or target.exists():
        raise ValueError("源数据库无效或目标已存在，未覆盖任何数据。")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="legacy-copy-", suffix=".sqlite3", dir=target.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as old, closing(sqlite3.connect(temporary)) as new:
            if not old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'").fetchone():
                raise ValueError("源文件不是可识别的指南数据库。")
            old.backup(new)
            if new.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("备份完整性校验失败。")
        # Atomic creation fails if another process created the destination meanwhile.
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    try:
        print("已保留原数据库并迁移副本至", migrate(args.source, args.destination))
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.exit(1, str(error) + "\n")

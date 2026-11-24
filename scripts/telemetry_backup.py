"""Offline/local backup and restore utility. Backups can contain private telemetry."""
import argparse
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def copy_verified(source, destination):
    source=Path(source).resolve()
    destination=Path(destination).resolve()
    if not source.is_file() or source==destination or destination.exists():
        raise ValueError("Source must exist and destination must be a new file")
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".aeris-backup-",dir=destination.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(source.as_uri()+"?mode=ro",uri=True)) as src:
            try:
                with closing(sqlite3.connect(temp)) as dst:
                    try:
                        src.backup(dst)
                        if dst.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:
                            raise ValueError("SQLite integrity check failed")
                        if dst.execute("PRAGMA foreign_key_check").fetchone() is not None:
                            raise ValueError("Foreign key check failed")
                        if dst.execute("PRAGMA user_version").fetchone()[0] not in (1,2,3):
                            raise ValueError("Unsupported schema version")
                    finally:
                        dst.close()
            finally:
                src.close()
        # Atomic no-clobber publication, including concurrent destination creation.
        os.link(temp,destination)
    finally:
        Path(temp).unlink(missing_ok=True)
    return destination


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args()
    print(copy_verified(args.source,args.destination))

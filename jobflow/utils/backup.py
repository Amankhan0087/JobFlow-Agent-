"""
Auto-backup jobflow.db — run daily via cron or APScheduler.
Keeps last 7 backups, deletes older ones.
"""
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "jobflow.db"
BACKUP_DIR = Path(__file__).parent.parent.parent / "backups"


def backup():
    if not DB_PATH.exists():
        return
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"jobflow_{stamp}.db"
    shutil.copy2(DB_PATH, dest)

    # Keep only last 7
    backups = sorted(BACKUP_DIR.glob("jobflow_*.db"))
    for old in backups[:-7]:
        old.unlink()

    print(f"Backup saved: {dest.name}")


if __name__ == "__main__":
    backup()

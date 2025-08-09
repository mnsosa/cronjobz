import os
import sqlite3
from pathlib import Path

from cronjobz.runner import execute_job
from cronjobz.storage_sqlite import init_db


def test_execute_job_inserts_row(tmp_path: Path):
    db = tmp_path / "runs.sqlite"
    init_db(db)

    script = tmp_path / "ok.sh"
    script.write_text("echo hello\n")
    os.chmod(script, 0o755)

    code = execute_job(name="daily-task", script=str(script), db_path=db)
    assert code == 0

    with sqlite3.connect(db) as cx:
        row = cx.execute(
            "SELECT name, script, exit_code FROM job_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row == ("daily-task", str(script), 0)

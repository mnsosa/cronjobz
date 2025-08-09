import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from cronjobz.storage_sqlite import JobRun, init_db, save_run


def test_init_db_creates_table(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_db(db)
    assert db.exists()
    with sqlite3.connect(db) as cx:
        row = cx.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='job_runs'"
        ).fetchone()
    assert row is not None


def test_save_run_persists_fields(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_db(db)

    start = datetime(2024, 1, 1, 12, 0, 0)
    end = start + timedelta(seconds=5)

    run = JobRun(
        name="daily-task",
        script="/bin/bash /tmp/script.sh",
        exit_code=0,
        started_at=start,
        finished_at=end,
        duration_seconds=5.0,
        stdout="OK",
        stderr="",
    )

    save_run(run, db)

    with sqlite3.connect(db) as cx:
        data = cx.execute(
            "SELECT name, script, exit_code, started_at, finished_at, duration_seconds, stdout, stderr "
            "FROM job_runs"
        ).fetchone()

    assert data[0] == "daily-task"
    assert data[1].endswith("/tmp/script.sh")
    assert data[2] == 0
    assert data[3] == start.isoformat()
    assert data[4] == end.isoformat()
    assert data[5] == 5.0
    assert data[6] == "OK"
    assert data[7] == ""

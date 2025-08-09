import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_DEFAULT_DB = Path(".data/cronjobz.sqlite")


@dataclass
class JobRun:
    name: str
    script: str
    exit_code: int
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    stdout: str
    stderr: str


def _db_path(db_path: Path | None) -> Path:
    return Path(db_path) if db_path else _DEFAULT_DB


def init_db(db_path: Path | None = None) -> None:
    db = _db_path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as cx:
        cx.execute("""CREATE TABLE IF NOT EXISTS job_runs(
            id INTEGER PRIMARY KEY,
            name TEXT, script TEXT, exit_code INT,
            started_at TEXT, finished_at TEXT, duration_seconds REAL,
            stdout TEXT, stderr TEXT
        )""")


def save_run(run: JobRun, db_path: Path | None = None) -> None:
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        cx.execute(
            """INSERT INTO job_runs
          (name,script,exit_code,started_at,finished_at,duration_seconds,stdout,stderr)
          VALUES (?,?,?,?,?,?,?,?)""",
            (
                run.name,
                run.script,
                run.exit_code,
                run.started_at.isoformat(),
                run.finished_at.isoformat(),
                run.duration_seconds,
                run.stdout,
                run.stderr,
            ),
        )

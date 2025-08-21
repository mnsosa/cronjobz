import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

_DEFAULT_DB = Path(".data/cronjobz.sqlite")


class JobStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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


@dataclass
class RunningJobRun:
    name: str
    script: str
    started_at: datetime


@dataclass
class JobRunRow:
    id: int
    name: str
    script: str
    exit_code: int | None
    started_at: str
    finished_at: str | None
    duration_seconds: float | None
    status: str


def _db_path(db_path: Path | None) -> Path:
    return Path(db_path) if db_path else _DEFAULT_DB


def init_db(db_path: Path | None = None) -> None:
    db = _db_path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as cx:
        # First create table with old schema if it doesn't exist
        cx.execute("""CREATE TABLE IF NOT EXISTS job_runs(
            id INTEGER PRIMARY KEY,
            name TEXT, script TEXT, exit_code INT,
            started_at TEXT, finished_at TEXT, duration_seconds REAL,
            stdout TEXT, stderr TEXT
        )""")

        # Add status column if it doesn't exist (migration)
        try:
            cx.execute("ALTER TABLE job_runs ADD COLUMN status TEXT DEFAULT 'completed'")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Make columns nullable for running jobs (SQLite doesn't support ALTER COLUMN)
        # We'll handle this in the application logic instead


def start_job_run(run: RunningJobRun, db_path: Path | None = None) -> int:
    """Start a job run and return its ID."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        cursor = cx.execute(
            """INSERT INTO job_runs
          (name, script, started_at, status, exit_code, finished_at, duration_seconds, stdout, stderr)
          VALUES (?, ?, ?, ?, NULL, NULL, NULL, '', '')""",
            (
                run.name,
                run.script,
                run.started_at.isoformat(),
                JobStatus.RUNNING.value,
            ),
        )
        return cursor.lastrowid


def finish_job_run(run_id: int, exit_code: int, finished_at: datetime, stdout: str, stderr: str, db_path: Path | None = None) -> None:
    """Finish a job run by updating its completion details."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        # Get the started_at time to calculate duration
        row = cx.execute("SELECT started_at FROM job_runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise ValueError(f"Job run with id {run_id} not found")

        started_at = datetime.fromisoformat(row[0])
        duration_seconds = (finished_at - started_at).total_seconds()
        status = JobStatus.COMPLETED.value if exit_code == 0 else JobStatus.FAILED.value

        cx.execute(
            """UPDATE job_runs SET
               exit_code = ?, finished_at = ?, duration_seconds = ?,
               stdout = ?, stderr = ?, status = ?
               WHERE id = ?""",
            (exit_code, finished_at.isoformat(), duration_seconds, stdout, stderr, status, run_id),
        )


def save_run(run: JobRun, db_path: Path | None = None) -> None:
    """Legacy function - saves a completed job run directly."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        status = JobStatus.COMPLETED.value if run.exit_code == 0 else JobStatus.FAILED.value
        cx.execute(
            """INSERT INTO job_runs
          (name,script,exit_code,started_at,finished_at,duration_seconds,stdout,stderr,status)
          VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                run.name,
                run.script,
                run.exit_code,
                run.started_at.isoformat(),
                run.finished_at.isoformat(),
                run.duration_seconds,
                run.stdout,
                run.stderr,
                status,
            ),
        )


def list_runs(limit: int = 200, db_path: Path | None = None) -> list[JobRunRow]:
    """Return last N runs (descending by id)."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        rows: Iterable[tuple] = cx.execute(
            """SELECT id, name, script, exit_code, started_at, finished_at, duration_seconds,
                      COALESCE(status, 'completed') as status
               FROM job_runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        return [
            JobRunRow(
                id=r[0],
                name=r[1],
                script=r[2],
                exit_code=r[3],
                started_at=r[4],
                finished_at=r[5],
                duration_seconds=float(r[6]) if r[6] is not None else None,
                status=r[7],
            )
            for r in rows
        ]


def list_running_jobs(db_path: Path | None = None) -> list[JobRunRow]:
    """Return all currently running jobs."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        rows: Iterable[tuple] = cx.execute(
            """SELECT id, name, script, exit_code, started_at, finished_at, duration_seconds, status
               FROM job_runs WHERE status = ? ORDER BY started_at DESC""",
            (JobStatus.RUNNING.value,),
        )
        return [
            JobRunRow(
                id=r[0],
                name=r[1],
                script=r[2],
                exit_code=r[3],
                started_at=r[4],
                finished_at=r[5],
                duration_seconds=float(r[6]) if r[6] is not None else None,
                status=r[7],
            )
            for r in rows
        ]


def get_run_logs(run_id: int, db_path: Path | None = None) -> tuple[str, str]:
    """Return (stdout, stderr) for a run id."""
    db = _db_path(db_path)
    with sqlite3.connect(db) as cx:
        row = cx.execute("SELECT stdout, stderr FROM job_runs WHERE id = ?", (run_id,)).fetchone()
    return (row[0], row[1]) if row else ("", "")

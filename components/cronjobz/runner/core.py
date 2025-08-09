from pathlib import Path

from cronjobz.shell import run as run_cmd
from cronjobz.storage_sqlite import JobRun, init_db, save_run


def execute_job(name: str, script: str, db_path: Path | None = None) -> int:
    """Run the script and persist metadata into SQLite."""
    init_db(db_path)
    result = run_cmd(["/bin/bash", script])
    save_run(
        JobRun(
            name=name,
            script=script,
            exit_code=result.exit_code,
            started_at=result.started_at,
            finished_at=result.finished_at,
            duration_seconds=result.duration_seconds,
            stdout=result.stdout,
            stderr=result.stderr,
        ),
        db_path=db_path,
    )
    return result.exit_code

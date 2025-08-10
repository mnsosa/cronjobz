from pathlib import Path

from cronjobz import shell, storage_sqlite


def execute_job(name: str, script: str, db_path: Path | None = None) -> int:
    """Run the script and persist metadata into SQLite."""
    storage_sqlite.init_db(db_path)
    result = shell.run(script.split(" "))
    storage_sqlite.save_run(
        storage_sqlite.JobRun(
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

from datetime import datetime
from pathlib import Path

from cronjobz import shell, storage_sqlite


def execute_job(name: str, script: str, db_path: Path | None = None) -> int:
    """Run the script and persist metadata into SQLite."""
    storage_sqlite.init_db(db_path)

    # Start tracking the job
    running_job = storage_sqlite.RunningJobRun(
        name=name,
        script=script,
        started_at=datetime.now(),
    )
    job_id = storage_sqlite.start_job_run(running_job, db_path=db_path)

    try:
        # Execute the script
        result = shell.run(script.split(" "))

        # Finish tracking the job
        storage_sqlite.finish_job_run(
            run_id=job_id,
            exit_code=result.exit_code,
            finished_at=result.finished_at,
            stdout=result.stdout,
            stderr=result.stderr,
            db_path=db_path,
        )

        return result.exit_code
    except Exception as e:
        # If something goes wrong, mark the job as failed
        storage_sqlite.finish_job_run(
            run_id=job_id,
            exit_code=1,
            finished_at=datetime.now(),
            stdout="",
            stderr=f"Job execution failed: {str(e)}",
            db_path=db_path,
        )
        raise

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from cronjobz.storage_sqlite import (
    JobStatus,
    RunningJobRun,
    finish_job_run,
    init_db,
    list_running_jobs,
    list_runs,
    start_job_run,
)


def test_start_job_run_creates_running_record(tmp_path: Path):
    """Test that starting a job creates a running record in the database."""
    db = tmp_path / "test.sqlite"
    init_db(db)

    start_time = datetime(2024, 1, 1, 12, 0, 0)
    running_job = RunningJobRun(
        name="test-task",
        script="/bin/echo hello",
        started_at=start_time,
    )

    job_id = start_job_run(running_job, db)

    # Verify the record was created
    with sqlite3.connect(db) as cx:
        row = cx.execute(
            "SELECT name, script, started_at, status, exit_code, finished_at FROM job_runs WHERE id = ?",
            (job_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == "test-task"
    assert row[1] == "/bin/echo hello"
    assert row[2] == start_time.isoformat()
    assert row[3] == JobStatus.RUNNING.value
    assert row[4] is None  # exit_code should be NULL
    assert row[5] is None  # finished_at should be NULL


def test_finish_job_run_updates_record(tmp_path: Path):
    """Test that finishing a job updates the record with completion details."""
    db = tmp_path / "test.sqlite"
    init_db(db)

    # Start a job
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    running_job = RunningJobRun(
        name="test-task",
        script="/bin/echo hello",
        started_at=start_time,
    )
    job_id = start_job_run(running_job, db)

    # Finish the job
    finish_time = start_time + timedelta(seconds=5)
    finish_job_run(
        run_id=job_id,
        exit_code=0,
        finished_at=finish_time,
        stdout="hello\n",
        stderr="",
        db_path=db,
    )

    # Verify the record was updated
    with sqlite3.connect(db) as cx:
        row = cx.execute(
            "SELECT exit_code, finished_at, duration_seconds, stdout, stderr, status FROM job_runs WHERE id = ?",
            (job_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == 0  # exit_code
    assert row[1] == finish_time.isoformat()  # finished_at
    assert row[2] == 5.0  # duration_seconds
    assert row[3] == "hello\n"  # stdout
    assert row[4] == ""  # stderr
    assert row[5] == JobStatus.COMPLETED.value  # status


def test_finish_job_run_with_failure(tmp_path: Path):
    """Test that finishing a job with non-zero exit code marks it as failed."""
    db = tmp_path / "test.sqlite"
    init_db(db)

    # Start a job
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    running_job = RunningJobRun(
        name="test-task",
        script="/bin/false",
        started_at=start_time,
    )
    job_id = start_job_run(running_job, db)

    # Finish the job with failure
    finish_time = start_time + timedelta(seconds=1)
    finish_job_run(
        run_id=job_id,
        exit_code=1,
        finished_at=finish_time,
        stdout="",
        stderr="command failed",
        db_path=db,
    )

    # Verify the record was updated with failed status
    with sqlite3.connect(db) as cx:
        row = cx.execute(
            "SELECT exit_code, status FROM job_runs WHERE id = ?",
            (job_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == 1  # exit_code
    assert row[1] == JobStatus.FAILED.value  # status


def test_list_running_jobs(tmp_path: Path):
    """Test that we can list currently running jobs."""
    db = tmp_path / "test.sqlite"
    init_db(db)

    # Start multiple jobs
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Running job 1
    running_job1 = RunningJobRun(
        name="running-task-1",
        script="/bin/sleep 10",
        started_at=start_time,
    )
    job_id1 = start_job_run(running_job1, db)

    # Running job 2
    running_job2 = RunningJobRun(
        name="running-task-2",
        script="/bin/sleep 20",
        started_at=start_time + timedelta(seconds=1),
    )
    job_id2 = start_job_run(running_job2, db)

    # Completed job
    running_job3 = RunningJobRun(
        name="completed-task",
        script="/bin/echo done",
        started_at=start_time + timedelta(seconds=2),
    )
    job_id3 = start_job_run(running_job3, db)
    finish_job_run(
        run_id=job_id3,
        exit_code=0,
        finished_at=start_time + timedelta(seconds=3),
        stdout="done\n",
        stderr="",
        db_path=db,
    )

    # Get running jobs
    running_jobs = list_running_jobs(db)

    # Should only return the 2 running jobs, ordered by started_at DESC
    assert len(running_jobs) == 2
    assert running_jobs[0].name == "running-task-2"
    assert running_jobs[0].status == JobStatus.RUNNING.value
    assert running_jobs[0].exit_code is None
    assert running_jobs[0].finished_at is None

    assert running_jobs[1].name == "running-task-1"
    assert running_jobs[1].status == JobStatus.RUNNING.value


def test_list_runs_includes_status(tmp_path: Path):
    """Test that list_runs includes the status column."""
    db = tmp_path / "test.sqlite"
    init_db(db)

    # Start and finish a job
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    running_job = RunningJobRun(
        name="test-task",
        script="/bin/echo test",
        started_at=start_time,
    )
    job_id = start_job_run(running_job, db)
    finish_job_run(
        run_id=job_id,
        exit_code=0,
        finished_at=start_time + timedelta(seconds=1),
        stdout="test\n",
        stderr="",
        db_path=db,
    )

    # Get all runs
    runs = list_runs(db_path=db)

    assert len(runs) == 1
    assert runs[0].status == JobStatus.COMPLETED.value
    assert runs[0].exit_code == 0
    assert runs[0].duration_seconds == 1.0
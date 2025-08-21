import sqlite3
from pathlib import Path

from cronjobz.runner import execute_job
from cronjobz.storage_sqlite import JobStatus, init_db, list_running_jobs, list_runs


def test_execute_job_tracks_lifecycle(tmp_path: Path):
    """Test that execute_job properly tracks the job lifecycle."""
    db = tmp_path / "test.sqlite"
    
    # Execute a simple job
    exit_code = execute_job(
        name="test-echo",
        script="echo 'hello world'",
        db_path=db,
    )
    
    # Verify job completed successfully
    assert exit_code == 0
    
    # Verify no running jobs remain
    running_jobs = list_running_jobs(db_path=db)
    assert len(running_jobs) == 0
    
    # Verify completed job was recorded
    completed_jobs = list_runs(limit=10, db_path=db)
    assert len(completed_jobs) == 1
    
    job = completed_jobs[0]
    assert job.name == "test-echo"
    assert job.script == "echo 'hello world'"
    assert job.status == JobStatus.COMPLETED.value
    assert job.exit_code == 0
    assert job.finished_at is not None
    assert job.duration_seconds is not None
    assert job.duration_seconds > 0


def test_execute_job_handles_failure(tmp_path: Path):
    """Test that execute_job properly handles job failures."""
    db = tmp_path / "test.sqlite"
    
    # Execute a failing job
    exit_code = execute_job(
        name="test-failure",
        script="false",  # This will fail
        db_path=db,
    )
    
    # Verify job failed
    assert exit_code == 1
    
    # Verify no running jobs remain
    running_jobs = list_running_jobs(db_path=db)
    assert len(running_jobs) == 0
    
    # Verify failed job was recorded
    completed_jobs = list_runs(limit=10, db_path=db)
    assert len(completed_jobs) == 1
    
    job = completed_jobs[0]
    assert job.name == "test-failure"
    assert job.script == "false"
    assert job.status == JobStatus.FAILED.value
    assert job.exit_code == 1
    assert job.finished_at is not None


def test_database_migration_adds_status_column(tmp_path: Path):
    """Test that init_db properly adds the status column to existing databases."""
    db = tmp_path / "test.sqlite"
    
    # Create database with old schema
    with sqlite3.connect(db) as cx:
        cx.execute("""CREATE TABLE job_runs(
            id INTEGER PRIMARY KEY,
            name TEXT, script TEXT, exit_code INT,
            started_at TEXT, finished_at TEXT, duration_seconds REAL,
            stdout TEXT, stderr TEXT
        )""")
        
        # Insert an old record
        cx.execute(
            """INSERT INTO job_runs 
               (name, script, exit_code, started_at, finished_at, duration_seconds, stdout, stderr)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("old-job", "echo old", 0, "2024-01-01T10:00:00", "2024-01-01T10:00:01", 1.0, "old", "")
        )
    
    # Run init_db to migrate
    init_db(db)
    
    # Verify status column was added and defaults to 'completed'
    with sqlite3.connect(db) as cx:
        row = cx.execute("SELECT status FROM job_runs WHERE name = 'old-job'").fetchone()
        assert row[0] == "completed"
        
        # Verify we can query with COALESCE for backwards compatibility
        row = cx.execute(
            "SELECT COALESCE(status, 'completed') as status FROM job_runs WHERE name = 'old-job'"
        ).fetchone()
        assert row[0] == "completed"
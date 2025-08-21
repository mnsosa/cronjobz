import typer
from cronjobz.runner import execute_job
from cronjobz.storage_sqlite import list_running_jobs, list_runs

app = typer.Typer()


@app.command()
def run(name: str, script: str) -> None:
    """Execute a job and track its progress."""
    code = execute_job(name=name, script=script)
    raise typer.Exit(code)


@app.command("list")
def list_jobs(
    running: bool = typer.Option(False, "--running", "-r", help="Show only running jobs"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of jobs to show"),
) -> None:
    """List job runs."""
    if running:
        jobs = list_running_jobs()
        typer.echo("Currently running jobs:")
        if not jobs:
            typer.echo("No jobs are currently running.")
            return
    else:
        jobs = list_runs(limit=limit)
        typer.echo(f"Recent job runs (last {len(jobs)}):")
        if not jobs:
            typer.echo("No job runs found.")
            return

    for job in jobs:
        status_symbol = "🟡" if job.status == "running" else ("✅" if job.exit_code == 0 else "❌")
        duration_str = f"{job.duration_seconds:.1f}s" if job.duration_seconds else "running..."
        typer.echo(f"{status_symbol} {job.name} ({duration_str}) - {job.script[:50]}{'...' if len(job.script) > 50 else ''}")

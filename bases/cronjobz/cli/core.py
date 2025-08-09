import typer
from cronjobz.runner import execute_job

app = typer.Typer()


@app.command()
def run(name: str, script: str) -> None:
    code = execute_job(name=name, script=script)
    raise typer.Exit(code)

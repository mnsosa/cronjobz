import subprocess
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float


def run(cmd: list[str]) -> RunResult:
    start = datetime.now()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    end = datetime.now()
    return RunResult(
        exit_code=proc.returncode,
        stdout=out,
        stderr=err,
        started_at=start,
        finished_at=end,
        duration_seconds=(end - start).total_seconds(),
    )

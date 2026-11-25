import os
from pathlib import Path

from prometheus_client import multiprocess


def on_starting(server):
    metrics_directory = Path(os.environ["PROMETHEUS_MULTIPROC_DIR"])
    metrics_directory.mkdir(parents=True, exist_ok=True)
    for path in metrics_directory.iterdir():
        if path.is_file():
            path.unlink()


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)

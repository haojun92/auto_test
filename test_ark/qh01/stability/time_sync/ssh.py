import threading
import time
from pathlib import Path

import click
from loguru import logger

from test_ark.qh01.ssh import J3A, J3B, TDA4

event = threading.Event()


def func(ssh: TDA4 | J3B | J3A):
    while True:
        event.wait()
        _, out, _ = ssh.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        logger.success(f"{ssh.__class__.__name__}, {out.strip()}")
        event.clear()


def main():
    threads = [
        threading.Thread(target=lambda: func(TDA4()), daemon=True),
        threading.Thread(target=lambda: func(J3B()), daemon=True),
        threading.Thread(target=lambda: func(J3A()), daemon=True),
    ]
    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(5)
            event.set()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")


@click.command()
@click.option(
    "--log-path",
    type=str,
    default=(Path(__file__).parent / "log/qh01/stability/time_sync.log").as_posix(),
    help="日志存储路径",
)
def cli(log_path: str):
    """长稳测试-时间同步_ssh获取时间并记录到日志中"""
    logger.add(log_path, level="SUCCESS")
    main()


if __name__ == "__main__":
    cli()

from pathlib import Path

import click
from loguru import logger

from test_ark.qh01.ssh import TDA4
from test_ark.qh01.stability import stability_testing


def main():
    with TDA4() as ssh:
        _, out, _ = ssh.exec_command("cat /sys/class/thermal/thermal_zone0/temp")
        logger.success(out)


@click.command()
@click.option("--interval", type=int, default=30, help="测试时间间隔")
@click.option(
    "--log-path",
    type=str,
    default=(Path(__file__).parent / "log/qh01/stability/tda4/temperature.log").as_posix(),
    help="日志存储路径",
)
def cli(interval: int, log_path: str):
    """长稳测试-TDA4-Temperature"""
    logger.add(log_path)
    stability_testing(main, interval=interval)


if __name__ == "__main__":
    cli()

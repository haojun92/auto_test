import datetime

import click
from loguru import logger

from test_ark.qh01.ssh import J3A, J3B, TDA4


def download_logs(connector, local_dir: str):
    logger.info(f"Downloading log of {connector.__name__}...")
    if connector.is_online():
        connector().download_logs(local_dir=local_dir)
    else:
        logger.warning(f"{connector.__name__} is offline")


def main(hostnames: list[str]) -> None:
    date: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if "TDA4" in hostnames:
        download_logs(TDA4, local_dir=f"logs/{date}")

    if "J3B" in hostnames:
        download_logs(J3B, local_dir=f"logs/{date}")

    if "J3A" in hostnames:
        download_logs(J3A, local_dir=f"logs/{date}")


@click.command()
@click.option("-h", "--hostnames", multiple=True, help="Hostnames to check")
def cli(hostnames: list[str]) -> None:
    """下载目标芯片上的log文件"""
    main(hostnames=hostnames or ["TDA4", "J3B", "J3A"])


if __name__ == "__main__":
    cli()

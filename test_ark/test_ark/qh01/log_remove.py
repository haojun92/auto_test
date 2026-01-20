import click
from loguru import logger

from test_ark.qh01.ssh import J3A, J3B, TDA4


def rm(connector):
    logger.info(f"Removing log of {connector.__name__}...")
    if connector.is_online():
        connector().exec_command("rm -rf /userdata/log")
    else:
        logger.warning(f"{connector.__name__} is offline")


def main(hostnames: list[str]) -> None:
    if "TDA4" in hostnames:
        rm(TDA4)

    if "J3B" in hostnames:
        rm(J3B)

    if "J3A" in hostnames:
        rm(J3A)


@click.command()
@click.option("-h", "--hostnames", multiple=True, help="Hostnames to check")
def cli(hostnames: list[str]) -> None:
    """删除目标芯片上的log文件"""
    main(hostnames=hostnames or ["TDA4", "J3B", "J3A"])


if __name__ == "__main__":
    cli()

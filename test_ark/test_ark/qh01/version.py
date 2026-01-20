import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from test_ark.qh01.ssh import J3A, J3B, TDA4, J3Mono

cmds = {
    "TDA4": [
        "cat /etc/*version",
        "export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH && hm_bootctrl_tool getcurrentslot",
        "export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH && hm_bootctrl_tool info",
        "cd /opt/qh01/target && . ./setenv.bash && ./bin/holo_ota/tda4_update_mcu -v",
        "export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH && cd /opt/qh01/target && . ./setenv.bash && ./bin/holo_ota/upgradeTool -g",  # noqa: E501
    ],
    "J3B": [
        "cat /etc/*version",
        "cat /mnt/adas/adas-rt/version",
        "hrut_otastatus g partstatus",
    ],
    "J3A": [
        "cat /etc/*version",
        "cat /mnt/adas/adas-rt/version",
        "hrut_otastatus g partstatus",
    ],
    "J3Mono":[
        "cat /etc/*version",
        "cat /mnt/adas/adas-rt/version",
        "hrut_otastatus g partstatus",
    ],
}


def version_of(connector) -> list[tuple[str, str, str] | None]:
    logger.info(f"Checking {connector.__name__} version...")
    rows: list[tuple[str, str, str] | None] = [(connector.__name__, "", "")]
    if connector.is_online():
        with connector() as ssh:
            for cmd in cmds[connector.__name__]:
                _, out, _ = ssh.exec_command(cmd)
                rows.append(("", cmd, out))
    else:
        logger.warning(f"{connector.__name__} is offline")
        rows.append(("", "", "Offline"))
    rows.append(None)
    return rows


def draw_table(rows: list[tuple[str, str, str] | None]):
    table = Table()
    table.add_column("Host", no_wrap=True)
    table.add_column("Command")
    table.add_column("Value")
    for row in rows:
        if row is None:
            table.add_section()
        else:
            table.add_row(*row)
    Console().print(table)


def main(hostnames: list[str]) -> None:
    rows = []
    # if "TDA4" in hostnames:
    #     rows.extend(version_of(TDA4))
    # if "J3B" in hostnames:
    #     rows.extend(version_of(J3B))
    # if "J3A" in hostnames:
    #     rows.extend(version_of(J3A))
    if "J3Mono" in hostnames:
        rows.extend(version_of(J3Mono))
    draw_table(rows)


@click.command()
@click.option("-h", "--hostnames", multiple=True, help="Hostnames to check")
def cli(hostnames: list[str]) -> None:
    """查看软件版本"""
    hostnames = hostnames or ["TDA4", "J3B", "J3A", "J3Mono"]
    main(hostnames)


if __name__ == "__main__":
    cli()

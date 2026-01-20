import datetime
import re
from pathlib import Path

import click
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib import ticker


def paint(x, y, title: str):
    plt.figure(figsize=(1366 / 80, 768 / 80), dpi=80)

    plt.title(title)
    plt.scatter(x, y, s=1)
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%dms"))
    plt.grid()

    plt.show()


def main(log_file: str):
    mcu_runtime_ms: list[int] = []
    last_line: str = ""
    for line in Path(log_file).read_text().splitlines():
        if "mcu_runtime_ms:" in line:
            pattern: re.Match = re.search(r"^mcu_runtime_ms:\s(?P<ms>\d+)", line)
            if pattern is None:
                continue
            now: int = int(pattern.group("ms"))
            if mcu_runtime_ms and mcu_runtime_ms[-1] > now:
                # mcu(sec/nsec):
                pattern: re.Match = re.search(r"\D+(?P<time_s>\d+)\s+(?P<time_ms>\d+)", last_line)
                date: str = datetime.datetime.fromtimestamp(int(pattern.group("time_s"))).strftime("%Y-%m-%d %H:%M:%S")
                last: int = mcu_runtime_ms[-1]
                logger.warning(f"{date=}, {now=}, {last=}")
            mcu_runtime_ms.append(now)

        last_line = line

    paint(x=[*range(len(mcu_runtime_ms))], y=mcu_runtime_ms, title="mcu_runtime_ms")


@click.command()
@click.option(
    "--log-file",
    type=click.Path(exists=True),
    required=True,
)
def cli(log_file: str):
    """根据/userdata/log/mcu_log/*.txt分析上电时间"""
    main(log_file)


if __name__ == "__main__":
    cli()

import re
from pathlib import Path

import click
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib import ticker


def statistic(dataframe: dict[str, float]):
    length = len(dataframe)
    average = round(sum(dataframe.values()) / length, 2)
    d_max = max(dataframe.values())
    d_min = min(dataframe.values())
    logger.info(f"{length=}, {average=}, max={d_max}, min={d_min}")


def paint(data: dict[str, float]):
    plt.figure(figsize=(1366 / 80, 768 / 80), dpi=80)

    plt.title("TDA4 Temperature")
    plt.scatter([*range(len(data))], [*data.values()], s=1)
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%d℃"))
    plt.grid()

    plt.show()


def main(log_path: str):
    d = {}
    for log_file in Path(log_path).parent.glob("temperature*.log"):
        logger.debug(f"Processing {log_file}")
        for line in log_file.open(encoding="utf-8").readlines():
            if s := re.search(r"print_exec_command.+\D(\d+(\.\d+)?)$", line):
                loading = float(s.groups()[0]) / 1000
                date: str = re.search(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line).group(0)
                d[date] = loading

    statistic(dataframe=d)

    paint(data=d)


@click.command()
@click.option(
    "--log-path",
    type=str,
    default=(Path(__file__).parent / "log/qh01/stability/tda4/temperature.log").as_posix(),
    help="日志存储路径",
)
def cli(log_path: str):
    """长稳测试-TDA4-Temperature作图"""
    main(log_path=log_path)


if __name__ == "__main__":
    cli()

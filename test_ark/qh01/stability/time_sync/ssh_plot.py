from datetime import datetime
from pathlib import Path

import click
from matplotlib import pyplot as plt
from matplotlib import ticker


def paint(dataframe: dict[str, list[float]], title):
    plt.figure(figsize=(1366 / 80, 768 / 80), dpi=80)
    plt.title(title)

    for label, data in dataframe.items():
        plt.scatter([*range(len(data))], data, s=1, label=label)

    plt.grid()
    plt.legend()
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1fms"))


def main(log_path: str):
    data: dict[str, list[float]] = {
        "TDA4": [],
        "J3B": [],
        "J3A": [],
    }
    for line in Path(log_path).read_text(encoding="utf-8").splitlines():
        for k in data:
            if k in line:
                date: str = line[-29:-6]
                data[k].append(datetime.timestamp(datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")))
                break

    #
    length: int = min(len(data[k]) for k in data)
    dataframe: dict[str, list[float]] = {k: [] for k in data}
    for i in range(length):
        average = sum(data[k][i] for k in data) / len(data)
        for k in data:
            dataframe[k].append((data[k][i] - average) * 1000)  # 单位：ms
    paint(dataframe=dataframe, title="Time Sync: ssh")

    plt.show()


@click.command()
@click.option(
    "--log-path",
    type=str,
    default=(Path(__file__).parent / "log/qh01/stability/time_sync.log").as_posix(),
    help="日志存储路径",
)
def cli(log_path: str):
    """长稳测试-时间同步_根据ssh日志作图"""
    main(log_path=log_path)


if __name__ == "__main__":
    cli()

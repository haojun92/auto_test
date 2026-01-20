import re
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import click
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib import ticker


def paint(data: dict[Any, float], title: str):
    plt.figure(figsize=(1366 / 80, 768 / 80), dpi=80)

    plt.title(title)
    plt.scatter([*range(len(data))], [*data.values()], s=1)
    plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1fms"))
    plt.grid()


class Config(TypedDict):
    channel_id: str
    frame_id: str


Raw = namedtuple("Raw", "ts channel_id frame_id raw")


def raw2datetime(raw: str) -> int | float:
    raw_lst: list[str] = raw.split()
    if raw_lst[0] == "20":  # 秒
        return int("".join((raw_lst[-4:])), 16)
    if raw_lst[0] == "28":  # 纳秒
        return int("".join((raw_lst[-4:])), 16) / 1000_000_000 + (int(raw_lst[3], 16) & 0b11)


def parse_file(log_file: Path, config_lst: list[Config]) -> list[Raw]:
    logger.info(f"Parsing {log_file}")
    data = []
    raw = {config["frame_id"]: 0 for config in config_lst}
    for line in log_file.open(encoding="utf-8").readlines():
        for config in config_lst:
            if f"{config['channel_id']} Rx        {config['frame_id']}" in line:
                pattern = (
                    r"^\s*(\d+\.\d+).+"
                    + config["channel_id"]
                    + r"\s+Rx\s+"
                    + config["frame_id"]
                    + r".+(([a-f0-9]{2}\s){7}[a-f0-9]{2})"
                )
                if s := re.search(pattern, line):
                    ts, raw_data, *_ = s.groups()
                    out = raw2datetime(raw_data)
                    if isinstance(out, int):  # s
                        raw[config["frame_id"]] = out
                    if isinstance(out, float):  # ns
                        raw[config["frame_id"]] += out
                        data.append(Raw(float(ts), config["channel_id"], config["frame_id"], raw[config["frame_id"]]))
    return data


def parse_files(log_path: str, config_lst: list[Config]) -> list[Raw]:
    data: list[Raw] = []
    for log_file in Path(log_path).rglob("*.asc"):
        data.extend(parse_file(log_file, config_lst))
    return data


def main(log_path: str):
    config_lst = [
        Config(channel_id="1", frame_id="515"),
        Config(channel_id="4", frame_id="518"),
    ]
    data: list[Raw] = parse_files(log_path, config_lst)

    for config in config_lst:
        target: dict[float, float] = {}
        for index, d in enumerate(data):
            if d.channel_id == config["channel_id"] and d.frame_id == config["frame_id"]:
                target[d.ts] = d.raw

        out: dict[float, float] = {}
        keys = [*target.keys()]
        for index, k in enumerate(target.keys()):
            if index <= 8:  # 前4s(8帧)存在波动，不纳入统计范围
                continue
            last_k = keys[index - 1]
            delta_ts = k - last_k
            delta_raw = target[k] - target[last_k]
            out[k] = (delta_raw - delta_ts) * 1000  # 单位：ms

            if out[k] > 600:  # 理想情况下out[k]趋近于0，此处判断大于600ms的为异常数据
                logger.warning(
                    f"{datetime.fromtimestamp(target[k]).strftime('%Y-%m-%d %H:%M:%S.%f')}与上一帧出现时间跳变，跳变间隔={out[k]}，"
                    f"报文录制时间={k}, 上一帧报文录制时间={last_k}, "
                    f"报文内容时间={target[k]}, 上一帧报文内容时间={target[last_k]}"
                )

        paint(
            data=out,
            title=f"Time Sync: channel_id({config['channel_id']})-frame_id(0x{int(config['frame_id'], 16):03x})",
        )

    plt.show()


@click.command()
@click.option(
    "--log-path",
    type=str,
    required=True,
    help="日志存储路径",
)
def cli(log_path: str):
    """分析时间同步报文的录制时间与内容时间差异"""
    main(log_path)


if __name__ == "__main__":
    cli()

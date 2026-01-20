import abc
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click
import matplotlib.pyplot as plt
from loguru import logger


def paint(x: list, y: list, title: str):
    plt.figure(figsize=(1366 / 80, 768 / 80), dpi=80)

    plt.title(title)
    plt.scatter(x, y, s=1)
    # plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter("%d%%"))
    plt.grid()


class Parser:
    def __init__(self):
        self.data = []

    @abc.abstractmethod
    def parse(self, line: str):
        ...

    @property
    def lines(self):
        return self.data

    def paint(self):
        ...


class ErrorParser(Parser):
    def parse(self, line: str):
        line = line.lower()
        if "err" in line or "error" in line:
            self.data.append(line)


class SendDiagnoseCodeParser(Parser):
    def parse(self, line: str):
        line = line.lower()
        if "send diagnose code:" in line:
            self.data.append(line)

    @property
    def lines(self):
        d: dict[str, list[str]] = defaultdict(list)
        for line in self.data:
            code: str = re.search(r"[a-z0-9]{8}", line).group()
            d[code].append(line)

        out: list[str] = []
        for k, v in d.items():
            out.append(f"{k}\n")
            out.extend(v)
        return out


class TemperatureParser(Parser):
    def parse(self, line: str):
        line = line.lower()
        if "temperature:" in line or "temprature:" in line:
            self.data.append(line)

    def paint(self):
        d: dict[str, list[float]] = defaultdict(list)
        for line in self.data:
            # date: str = re.search(r"\d{2}:\d{2}:\d{2}\.\d{6}", line).group(0)
            temperature = float(re.search(r"temprature: (\d+\.\d+)", line).group(1))
            d["temperature"].append(temperature)

        for k, v in d.items():
            paint(x=[*range(len(v))], y=v, title=f"{k}")


class CameraIDParser(Parser):
    def parse(self, line: str):
        line = line.lower()
        if "camera id :" in line:
            self.data.append(line)

    def paint(self):
        d: dict[str, list[float]] = defaultdict(list)
        d_camera: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for line in self.data:
            # date: str = re.search(r"\d{2}:\d{2}:\d{2}\.\d{6}", line).group(0)
            camera_id: str = re.search(r"camera id : (\d)", line).group(1)
            d_camera[camera_id]["average_fps"].append(float(re.search(r"average fps: (\d+(\.\d+)?)", line).group(1)))
            d_camera[camera_id]["delay"].append(float(re.search(r"delay: (\d+(\.\d+)?)", line).group(1)))
            d_camera[camera_id]["bpu_mem"].append(float(re.search(r"bpu_mem: (\d+(\.\d+)?)", line).group(1)))

            if camera_id == "0":
                d["cpu"].append(float(re.search(r"cpu: (\d+(\.\d+)?)", line).group(1)))
                d["mem"].append(float(re.search(r"mem: (\d+(\.\d+)?)", line).group(1)))

        for camera_id, data in d_camera.items():
            for k, v in data.items():
                paint(x=[*range(len(v))], y=v, title=f"{camera_id=}, {k}")
        for k, v in d.items():
            paint(x=[*range(len(v))], y=v, title=f"{k}")


def main(log_path: str, out_log_path: str):
    if not Path(log_path).exists():
        logger.error(f"{Path(log_path).absolute()} does not exist")

    parsers: list[Parser] = [
        ErrorParser(),
        SendDiagnoseCodeParser(),
        TemperatureParser(),
        CameraIDParser(),
    ]
    for log_file in Path(log_path).rglob("debug*"):
        logger.info(f"Parsing {log_file}")
        for line in log_file.open(encoding="utf-8").readlines():
            for parser in parsers:
                parser.parse(line)

    for parser in parsers:
        Path(out_log_path).mkdir(parents=True, exist_ok=True)
        (Path(out_log_path) / f"{parser.__class__.__name__}.log").open("w", encoding="utf-8").writelines(parser.lines)
        parser.paint()  # 作图
    plt.show()


@click.command()
@click.option(
    "--log-path",
    type=str,
    required=True,
    help="日志文件夹路径",
)
@click.option(
    "--out-log-path",
    type=str,
    default=f"logs/{datetime.now().strftime('%Y%m%d%H%M%S')}_app",
    help="输出日志文件夹路径",
)
def cli(log_path: str, out_log_path: str):
    """分析J3 app日志并保存错误日志到指定文件夹"""
    main(log_path=log_path, out_log_path=out_log_path)


if __name__ == "__main__":
    cli()

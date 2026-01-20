import csv
import json
from functools import cached_property
from pathlib import Path
from typing import List

import click
import matplotlib.pyplot as plt
from matplotlib import ticker


class APAPlot(object):
    def __init__(self, data: List[dict]):
        self.data = data

    @cached_property
    def x(self):
        return [json.loads(d["odo.position"].replace("'", '"'))["x"] for d in self.data]

    @cached_property
    def y(self):
        return [json.loads(d["odo.position"].replace("'", '"'))["y"] for d in self.data]

    @cached_property
    def max_x(self):
        return max(*self.x, max(point["x"] for box in self.slot for point in box))

    @cached_property
    def max_y(self):
        return max(*self.y, max(point["y"] for box in self.slot for point in box))

    @cached_property
    def slot(self) -> List[List[dict]]:
        return [
            [
                {k: float(v) for k, v in json.loads(data["slot.pos1"].replace("'", '"')).items()},
                {k: float(v) for k, v in json.loads(data["slot.pos2"].replace("'", '"')).items()},
                {k: float(v) for k, v in json.loads(data["slot.pos3"].replace("'", '"')).items()},
                {k: float(v) for k, v in json.loads(data["slot.pos4"].replace("'", '"')).items()},
            ]
            for data in self.data
        ]

    def paint(self, title: str = None):
        # plt.ion()

        plt.figure(figsize=(1920 / 80, 1080 / 80), dpi=80)
        if title:
            plt.title(title)
        # plt.xlim(0, int(self.max_x) + 1)
        # plt.ylim(0, int(self.max_y) + 1)
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(0.5))
        plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(0.5))
        plt.grid(True)

        # 绘制车位
        box_x = [point["x"] for point in self.slot[-1]]
        box_y = [point["y"] for point in self.slot[-1]]
        plt.plot(box_x + [box_x[0]], box_y + [box_y[0]], "g--", label="slot")

        # 绘制轨迹
        plt.plot(self.x, self.y, marker=".", label="ego trajectory")


def main(csv_file: str):
    APAPlot(data=[*csv.DictReader(Path(csv_file).open(encoding="utf-8"))]).paint(Path(csv_file).stem)

    plt.show()


@click.command()
@click.option("--csv-file", type=str, required=True, help="数据源csv文件路径")
def cli(csv_file: str):
    """APA绘制泊车轨迹"""
    main(csv_file=csv_file)


if __name__ == "__main__":
    cli()

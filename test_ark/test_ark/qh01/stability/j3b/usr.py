import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click
from loguru import logger


def main(log_path: str, out_log_file: str):
    if not Path(log_path).exists():
        logger.error(f"{Path(log_path).absolute()} does not exist")

    error_data = defaultdict(list)
    for log_file in Path(log_path).rglob("*.umsg"):
        logger.info(f"Parsing {log_file}")
        for line in log_file.open(encoding="utf-8").readlines():
            if err_type := re.search(r"\s(E/\w+)\s", line):
                error_data[err_type.groups()[0]].append(line)

    lines: list[str] = []
    for err_type, err_lines in error_data.items():
        lines.append(f"{err_type}\n")
        lines.extend([f"\t{err_line}" for err_line in err_lines])
    Path(out_log_file).open(mode="w", encoding="utf-8").writelines(lines)


@click.command()
@click.option(
    "--log-path",
    type=str,
    required=True,
    help="日志文件夹路径",
)
@click.option(
    "--out-log-file",
    type=str,
    default=f"logs/{datetime.now().strftime('%Y%m%d%H%M%S')}_usr.log",
    help="输出日志文件夹路径",
)
def cli(log_path: str, out_log_file: str):
    """分析J3 usr日志并保存错误日志到指定文件"""
    main(log_path=log_path, out_log_file=out_log_file)


if __name__ == "__main__":
    cli()

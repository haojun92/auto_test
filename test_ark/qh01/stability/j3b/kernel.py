from datetime import datetime
from pathlib import Path

import click
from loguru import logger


def main(log_path: str, out_log_file: str):
    if not Path(log_path).exists():
        logger.error(f"{Path(log_path).absolute()} does not exist")

    lines: list[str] = []
    for log_file in Path(log_path).rglob("*.kmsg"):
        logger.info(f"Parsing {log_file}")
        for line in log_file.open(encoding="utf-8").readlines():
            if "user.err" in line:
                lines.append(line)

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
    default=f"logs/{datetime.now().strftime('%Y%m%d%H%M%S')}_kernel.log",
    help="输出日志文件夹路径",
)
def cli(log_path: str, out_log_file: str):
    """分析J3 kernel日志并保存错误日志到指定文件"""
    main(log_path=log_path, out_log_file=out_log_file)


if __name__ == "__main__":
    cli()

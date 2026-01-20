import importlib
import sys
from pathlib import Path

import click
import dotenv
from click import Command
from loguru import logger

dotenv.load_dotenv()


@click.group()
@click.option("--log-level", default="INFO", help="日志等级")
@click.option("--log-file", help="日志文件路径")
@click.option("--log-file-level", help="日志文件等级")
def cli(log_level: str, log_file: str, log_file_level: str):
    """Testing Ark"""
    logger.remove(0)
    logger.add(sys.stderr, level=log_level)
    if log_file:
        logger.add(log_file, rotation="100 MB", level=log_file_level or log_level)


for file in Path(__file__).parent.rglob("*.py"):
    if file.name.startswith("_"):
        continue

    if name := ".".join(Path(file).relative_to(Path(__file__).parent).as_posix().replace("/", ".").split(".")[:-2]):
        module_name = f"{name}.{file.stem}"
        try:
            m = importlib.import_module(f".{module_name}", package=Path(__file__).parent.stem)
        except Exception as e:
            logger.error(e)
        else:
            if hasattr(m, "cli") and isinstance(m.cli, Command):
                cli.add_command(m.cli, name=module_name)

if __name__ == "__main__":
    cli()

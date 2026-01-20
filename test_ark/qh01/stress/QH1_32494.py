import click

from test_ark.qh01.ssh import J3B
from test_ark.qh01.stress import reset, stress_testing


def main(current: int, reset_method: str, *args, **kwargs):  # noqa
    remote_file = "/userdata/log/usr/message"
    with J3B() as ssh:
        ssh.exec_command("sync")
        ssh.download_file(remote_file, local_dir=f"./log/QH1-32494/{current}")
        ssh.exec_command(f"rm {remote_file}")

    reset(method=reset_method)


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=60, help="测试时间间隔")
@click.option("--reset-method", type=click.Choice(["doip", "power", "relay"]), required=True, help="重启方式")
def cli(count: int, interval: int, reset_method: str):
    """压力测试-QH1-32494"""
    stress_testing(main, count=count, interval=interval, reset_method=reset_method)


if __name__ == "__main__":
    cli()

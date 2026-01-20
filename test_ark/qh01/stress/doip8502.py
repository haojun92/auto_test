import time

import click
from loguru import logger
from udsoncan.services import (
    ControlDTCSetting,
    DiagnosticSessionControl,
    ReadDTCInformation,
)

from test_ark.qh01.doip import DoIP
from test_ark.qh01.stress import reset, stress_testing


def main(reset_method, *args, **kwargs):  # noqa
    with DoIP() as doip:
        doip.client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
        # for i in range(10):
        #     logger.info(f"{i + 1}, " + "-" * 80)
        #     doip.client.control_dtc_setting(ControlDTCSetting.SettingType.off)
        #     doip.client.clear_dtc()
        #     response = doip.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        #     assert list(response.data) == [0x02, 0x09]
        #     doip.client.control_dtc_setting(ControlDTCSetting.SettingType.on)
        #     time.sleep(3)
    reset(method=reset_method)


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=60, help="测试时间间隔")
@click.option("--reset-method", type=click.Choice(["doip", "power", "relay"]), required=True, help="重启方式")
def cli(count: int, interval: int, reset_method: str):
    """压力测试-doip8502"""
    stress_testing(main, count=count, interval=interval, reset_method=reset_method)


if __name__ == "__main__":
    cli()

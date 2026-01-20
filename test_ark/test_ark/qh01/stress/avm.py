import click
from loguru import logger
from udsoncan.services import ReadDTCInformation

from test_ark.qh01.doip import DoIP
from test_ark.qh01.stress import reset, stress_testing


def main(reset_method: str, *args, **kwargs):  # noqa
    with DoIP() as doip:
        response = doip.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        dtc_lst: list[bytes] = doip.read_dtc(response.data[2:])
        for index, dtc in enumerate(dtc_lst):  # 先打印一遍
            logger.warning(f"DTC{index}: {dtc.hex()}")
        for index, dtc in enumerate(dtc_lst):  # 再分析是否有目标故障
            # 出现预期故障（0x605200）且为"当前故障"（0x09）则停止测试
            if dtc[-1] == 0x09 and dtc[:-1].hex() == "605200":  # C205200->605200
                raise Exception("故障状态，请检查！")
        doip.client.change_session(0x03)
        doip.client.clear_dtc()

    reset(method=reset_method)


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=300, help="测试时间间隔")
@click.option("--reset-method", type=click.Choice(["doip", "power", "relay"]), required=True, help="重启方式")
def cli(count: int, interval: int, reset_method: str):
    """压力测试-AVM出图"""
    stress_testing(main, count=count, interval=interval, reset_method=reset_method)


if __name__ == "__main__":
    cli()

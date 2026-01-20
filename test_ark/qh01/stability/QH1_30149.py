import click
from loguru import logger
from udsoncan.services import ReadDTCInformation

from test_ark.qh01.doip import DoIP
from test_ark.qh01.stability import stability_testing


def main():
    with DoIP() as doip:
        doip.client.read_data_by_identifier(0x40A3)
        doip.client.read_data_by_identifier(0x40A4)
        doip.client.read_data_by_identifier(0x40A6)
        doip.client.read_data_by_identifier(0x40AB)
        doip.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        doip.client.clear_dtc()


@click.command()
@click.option("--interval", type=int, default=60, help="测试时间间隔")
def cli(interval: int):
    """长稳测试-QH1-30149"""
    logger.add("logs/test_ark/qh01/stability/QH1_30149.log")
    stability_testing(main, interval=interval)


if __name__ == "__main__":
    cli()

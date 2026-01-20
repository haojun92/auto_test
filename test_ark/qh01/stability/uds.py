import click
from loguru import logger
from udsoncan.services import ReadDTCInformation

from test_ark.qh01.doip import DoIP
from test_ark.qh01.stability import stability_testing


def main():
    with DoIP() as doip:
        for did in [
            0xF013,
            0xF089,
            0xF0F0,
            0xF0F1,
            0xF0F2,
            0xF0F3,
            0xF180,
            0xF184,
            0xF186,
            0xF187,
            0xF189,
            0xF18A,
            0xF18B,
            0xF18C,
            0xF190,
            0xF195,
            0xF289,
            0xF289,
            0xF289,
            0x4000,
            0x4080,
            0x4001,
            0x4002,
            0x4003,
            0x4004,
            0x4005,
            0x4006,
            0x4007,
            0xF011,
            0x4008,
            0x4009,
            0x400A,
            0x400B,
            0x400C,
            0x4010,
            0x4011,
            0x4013,
            0x4014,
            0x4014,
            0x4015,
            0x40A3,
            0x40A4,
            0x40A6,
            0x40A7,
            0x40AB,
            0x40AC,
            0x40AD,
            0x4017,
            0x4018,
            0x4020,
            0x4021,
        ]:
            response = doip.client.read_data_by_identifier(did)
            logger.info(response.service_data.values[did])
        doip.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        doip.client.clear_dtc()


@click.command()
@click.option("--interval", type=int, default=300, help="测试时间间隔")
def cli(interval: int):
    """长稳测试-DoIP"""
    logger.add("stability_testing.log", rotation="100 MB")
    stability_testing(main, interval=interval)


if __name__ == "__main__":
    cli()

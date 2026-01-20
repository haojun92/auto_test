import time
from functools import partial

import click
from loguru import logger
from pcan_ext.callbacks import (
    callback_rx_print,
    callback_tx_print,
    callback_tx_qh01_0x510,
    callback_tx_qh01_crc8,
)
from pcan_ext.pcan import PCan
from pcan_ext.typing import FrameID, NetworkName
from PCANBasic import PCAN_USBBUS1


def initialize(channel_name: NetworkName) -> None:
    PCan()[channel_name].rx["callbacks"] = [callback_rx_print]

    PCan()[channel_name].tx[FrameID(0x600)] = {
        "interval": 1000,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [callback_tx_print],
    }
    PCan()[channel_name].tx[FrameID(0x49D)] = {
        "interval": 100,
        "data": bytes([0, 0, 2, 0, 0, 0, 0, 0]),
        "callbacks": [
            partial(callback_tx_qh01_crc8, data_ids=[0x009C]),
            callback_tx_print,
        ],
    }
    PCan()[channel_name].tx[FrameID(0x510)] = {  # 时间同步报文，非必需
        "interval": 500,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [
            callback_tx_qh01_0x510,
            callback_tx_print,
        ],
    }

    PCan().start_all()


def main():
    logger.enable("pcan_ext")
    da = PCan().add_network(handle=PCAN_USBBUS1, is_fd=True)
    initialize(channel_name=da)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.warning("Ctrl+C pressed")
    finally:
        PCan().stop_all()


@click.command()
def cli() -> None:
    """NM激活工具"""
    main()


if __name__ == "__main__":
    cli()

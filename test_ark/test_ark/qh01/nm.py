import time
from datetime import datetime
from functools import partial

import click
from loguru import logger
from pcan_ext.callback import (
    callback_rx_print,
    callback_tx_print,
    callback_tx_qh01_crc8,
)
from pcan_ext.pcan import PCan
from pcan_ext.typing import FrameID
from PCANBasic import PCAN_USBBUS1

from test_ark.qh01.ssh import J3B, TDA4


def delta_t(t0, t1, datetime_format: str = "%Y-%m-%d %H:%M:%S.%f") -> float:
    datetime_t0 = datetime.strptime(t0, datetime_format)
    datetime_t1 = datetime.strptime(t1, datetime_format)
    return (datetime_t0 - datetime_t1).total_seconds()


def _test_time_sync() -> bool:
    tda4_datetime = TDA4.is_online() and TDA4().now()
    j3b_datetime = J3B.is_online() and J3B().now()
    return tda4_datetime and j3b_datetime and delta_t(tda4_datetime[:-4], j3b_datetime[:-4]) < 1.0


def main():
    # init
    logger.enable("pcan_ext")
    da = PCan().add_network(PCAN_USBBUS1, is_fd=True)
    PCan()[da].rx["callbacks"] = [callback_rx_print]

    PCan()[da].tx[FrameID(0x600)] = {
        "interval": 1000,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [callback_tx_print],
    }
    # PCan()[da].tx[FrameID(0x49D)] = {
    #     "interval": 100,
    #     "data": bytes([0, 0, 2, 0, 0, 0, 0, 0]),
    #     "callbacks": [partial(callback_tx_qh01_crc8, data_ids=[0x009C]), callback_tx_print],
    # }

    PCan().start_all()

    time.sleep(60)

    # 从0x600网络管理报文的默认周期1000ms开始，每隔60s设置一次0x600的周期为interval递增值，单次加10ms，直到interval周期达到30s
    # 此过程中可以测试到NM报文停发0ms-29000ms时，ECU的表现
    #   - 表现检测逻辑还没想好怎么写，估计需要单独建立线程处理，或者用另一个脚本
    #       - ping得通J3B
    #       - ping得通mcu
    #       - ping得通TC397
    #       - 诊断服务正常
    #       - AVM出图正常
    #       - 电流正常
    #       - SM状态正常，EM进程组正常
    #       - ...
    interval: int = 1000
    while interval < 30_000:
        interval += 10
        PCan()[da].tx[FrameID(0x600)]["interval"] = interval
        logger.info(f"Set interval to {interval}ms")
        time.sleep(interval / 1000)
        PCan()[da].tx[FrameID(0x600)]["interval"] = 1000
        time.sleep(60)


@click.command()
def cli():
    """网络管理测试"""
    main()


if __name__ == "__main__":
    cli()

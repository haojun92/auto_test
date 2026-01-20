import time
from datetime import datetime
from functools import partial
from pathlib import Path

import click
from loguru import logger
from pcan_ext.callbacks import (
    callback_tx_print,
    callback_tx_qh01_0x510,
    callback_tx_qh01_crc8,
)
from pcan_ext.pcan import PCan
from pcan_ext.typing import FrameID, NetworkName
from PCANBasic import PCAN_USBBUS1

from test_ark.qh01.log_download import download_logs
from test_ark.qh01.log_remove import rm
from test_ark.qh01.ssh import J3B, TDA4
from test_ark.qh01.stress import stress_testing

logger.add(
    f"./log/{Path(__file__).stem}/run.log",
    rotation="100 MB",
)
log = logger.bind(name=Path(__file__).stem)


def delta_t(t0, t1, datetime_format: str = "%Y-%m-%d %H:%M:%S.%f") -> float:
    datetime_t0 = datetime.strptime(t0, datetime_format)
    datetime_t1 = datetime.strptime(t1, datetime_format)
    return (datetime_t0 - datetime_t1).total_seconds()


def check_time():
    error_flag: bool = True
    tda4_datetime = j3b_datetime = None
    if TDA4.is_online():
        with TDA4() as ssh:
            _, tda4_datetime, _ = ssh.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
    else:
        logger.warning("TDA4 offline")
    if J3B.is_online():
        with J3B() as ssh:
            _, j3b_datetime, _ = ssh.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
    else:
        logger.warning("J3B offline")

    if tda4_datetime and j3b_datetime:
        if delta_t(tda4_datetime[:-4], j3b_datetime[:-4]) > 1.0:
            logger.warning(f"时间同步异常, {tda4_datetime=}, {j3b_datetime=}")
            error_flag = False
    else:
        error_flag = False
        logger.info("TDA4 or J3 offline")
    return error_flag


def test(network_name: NetworkName, current: int):
    logger.info("进入哨兵模式")
    PCan()[network_name].tx[FrameID(0x4FF)] = {
        "interval": 100,
        "data": bytes([0, 0, 2, 4, 0, 0, 0, 0]),
        "callbacks": [callback_tx_print],
    }
    PCan()[network_name].tx[FrameID(0x49D)]["data"] = bytes([0, 0, 0, 0, 0, 0, 0, 0])

    time.sleep(120)
    logger.info("退出哨兵模式")
    PCan()[network_name].tx[FrameID(0x4FF)]["data"] = bytes([0, 0, 0, 0, 0, 0, 0, 0])
    PCan()[network_name].tx[FrameID(0x49D)]["data"] = bytes([0, 0, 2, 0, 0, 0, 0, 0])
    time.sleep(20)
    logger.info("检查")

    if check_time():
        logger.info(f"{current} time passed")
    else:  # 如果存在异常，取日志
        logger.error(f"{current} time failed")
        download_logs(TDA4, f"log/{current}")
        rm(TDA4)


def main(count: int):
    logger.enable("pcan_ext")
    can1 = PCan().add_network(handle=PCAN_USBBUS1, is_fd=True)
    PCan()[can1].tx[FrameID(0x600)] = {
        "interval": 1000,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [],
    }
    PCan()[can1].tx[FrameID(0x49D)] = {
        "interval": 100,
        "data": bytes([0, 0, 2, 0, 0, 0, 0, 0]),
        "callbacks": [partial(callback_tx_qh01_crc8, data_ids=[0x009C])],
    }
    PCan()[can1].tx[FrameID(0x510)] = {
        "interval": 500,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [callback_tx_qh01_0x510],
    }

    PCan().start_all()
    # test
    stress_testing(test, count=count, interval=0, network_name=can1)


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
def cli(count: int):
    """压力测试-哨兵模式"""
    main(count=count)


if __name__ == "__main__":
    cli()

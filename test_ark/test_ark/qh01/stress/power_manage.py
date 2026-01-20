import copy
import functools
import re
import time
from collections.abc import Callable

import click
from loguru import logger
from pcan_ext.callbacks import callback_rx, callback_rx_print
from pcan_ext.pcan import PCan
from PCANBasic import PCAN_USBBUS2

from test_ark.power import Power
from test_ark.qh01.ssh import J3B, TDA4
from test_ark.qh01.stress import stress_testing


def get_tda4_camera_cmw_state() -> bool | dict:
    cmd = "ps -p $(ps -ef | grep -v grep | grep tda4_camera_cmw | awk -F' ' 'NR==1 {print $2}') -o %cpu,%mem | grep -v %CPU"  # noqa: E501
    with TDA4() as ssh:
        _, stdout, _ = ssh.exec_command(cmd)
    result = [i for i in re.split(r"\s", stdout) if i]
    return {
        "cpu": float(result[0]),
        "mem": float(result[1]),
    }


def check_tda4_camera_cmw_state() -> bool:
    if not TDA4.is_online():
        return False

    try:
        state = get_tda4_camera_cmw_state()
    except Exception as e:
        logger.exception(e)
    else:
        return state and 6.0 < state["cpu"] < 20.0 and 2.0 < state["mem"] < 20.0
    return False


def check_can() -> bool:
    logger.enable("pcan_ext")
    logger.debug("checking CAN(PCAN_USBBUS2)...")
    ch = PCan().add_network(handle=PCAN_USBBUS2, is_fd=True)
    PCan().networks[ch].rx["callbacks"] = [callback_rx, callback_rx_print]
    PCan().start_all()
    time.sleep(3)
    PCan().stop_all()
    result = len(PCan().networks[ch].rx["data"].keys()) > 1  # 默认会有FrameID=0x1的报文
    PCan().remove_network(ch)
    logger.debug(f"checking CAN...done, {result}")
    return result


def check(f, max_retries: int = 3, timeout: int = 10):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        logger.info("-" * 80)
        result: dict[str, bool] = {}
        for i in range(max_retries + 1):
            result = f(*args, **kwargs)
            for k, v in result.items():
                logger.info(f"{k} = {v}")
            if all(result.values()):
                logger.success("passed")
                break
            if i < max_retries:
                logger.error(f"failed, retry: {i + 1}/{max_retries}")
                time.sleep(timeout)
            else:
                logger.error(f"failed")
        logger.info("-" * 80)
        return result

    return wrapper


@check
def check_power_normal() -> dict[str, bool]:
    return {
        # "MCU_TC397": ping("192.168.1.131").success(),
        "SOC_J3B": J3B.is_online(),
        "SOC_TDA4": TDA4.is_online(),
        "Camera": check_tda4_camera_cmw_state(),
        "CAN": check_can(),
        "ETH": TDA4.is_online(),
    }


@check
def check_power_l1low() -> dict[str, bool]:
    return {
        # "MCU_TC397": not ping("192.168.1.131").success(),
        "SOC_J3B": not J3B.is_online(),
        "SOC_TDA4": not TDA4.is_online(),
        "Camera": not check_tda4_camera_cmw_state(),
        "CAN": check_can(),
        "ETH": not TDA4.is_online() and not J3B.is_online(),
    }


@check
def check_power_l2low() -> dict[str, bool]:
    return {
        # "MCU_TC397": not ping("192.168.1.131").success(),
        "SOC_J3B": not J3B.is_online(),
        "SOC_TDA4": not TDA4.is_online(),
        "Camera": not check_tda4_camera_cmw_state(),
        "CAN": not check_can(),
        "ETH": not TDA4.is_online() and not J3B.is_online(),
    }


@check
def check_power_l1high() -> dict[str, bool]:
    return {
        # "MCU_TC397": ping("192.168.1.131").success(),
        "SOC_J3B": J3B.is_online(),
        "SOC_TDA4": TDA4.is_online(),
        "Camera": check_tda4_camera_cmw_state(),
        "CAN": check_can(),
        "ETH": TDA4.is_online(),
    }


@check
def check_power_l2high() -> dict[str, bool]:
    return {
        # "MCU_TC397": not ping("192.168.1.131").success(),
        "SOC_J3B": not J3B.is_online(),
        "SOC_TDA4": not TDA4.is_online(),
        "Camera": not check_tda4_camera_cmw_state(),
        "CAN": not check_can(),
        "ETH": not TDA4.is_online() and not J3B.is_online(),
    }


def checker_mapping(volt: float) -> Callable:
    if volt <= 6:
        return check_power_l2low
    if 6 < volt <= 8:
        return check_power_l1low
    if 8 < volt <= 16:
        return check_power_normal
    if 16 < volt <= 18:
        return check_power_l1high
    if 18 < volt:
        return check_power_l2high


def dfs(lst: list):
    """Depth-First-Search"""
    d = {}
    for i in lst:
        tmp = copy.deepcopy(lst)
        tmp.remove(i)
        d[i] = tmp

    start = lst[0]
    result = [start]
    while True:
        if d[start]:
            start = d[start].pop()
            result.append(start)
        else:
            break
    return result


def pre_check():
    logger.info("前置条件检查")
    Power().v = 12.0
    checker = checker_mapping(12.0)
    assert all(checker().values()), "前置条件检查失败！"


def main(*args, **kwargs):  # noqa
    """电源管理检查"""
    pre_check()

    volts = [5.5, 6.5, 7.5, 8.5, 12.0, 15.5, 16.5, 17.5, 18.8]
    # pairs = permutations(volts, 2)
    # circles = circle(volts)
    # for pair in pairs:
    #     for index, item in enumerate(circles):
    #         if item == pair[0] and circles[index + 1] == pair[1]:
    #             break
    #     else:
    #         raise Exception("xxx")

    volts_chain = dfs(volts)
    total = len(volts_chain)
    for index, volt in enumerate(volts_chain):
        checker = checker_mapping(volt)
        logger.info(f"{index + 1}/{total}, {volt=}, {checker=}")
        Power().v = volt
        time.sleep(60)
        assert all(checker().values())


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=60, help="测试时间间隔")
def cli(count: int, interval: int):
    """压力测试-电源管理"""
    stress_testing(main, count=count, interval=interval)


if __name__ == "__main__":
    cli()

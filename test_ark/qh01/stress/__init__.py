import time
from collections.abc import Callable

from loguru import logger


def reset(method: str):
    logger.debug(f"Reset, {method=}")
    if method == "doip":
        from test_ark.qh01.doip import DoIP

        DoIP().hard_reset()
    if method == "power":
        from test_ark.power import Power

        Power().off()
        time.sleep(3)
        Power().on()
    if method == "relay":
        from test_ark.relay import Relay

        Relay().off()
        time.sleep(3)
        Relay().on()


def stress_testing(f: Callable, count: int, interval: float = 30, *args, **kwargs):
    """压力测试

    :param f: 测试函数
    :param count: 测试次数
    :param interval: 间隔时间
    :param args: 测试函数参数
    :param kwargs: 测试函数参数
    """
    try:
        for current in range(1, count + 1):
            logger.info("*" * 80 + f" {current:03d}/{count:03d}")

            f(current=current, count=count, interval=interval, *args, **kwargs)

            if current < count:
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")

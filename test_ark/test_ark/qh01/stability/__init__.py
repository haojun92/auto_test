import time
from collections.abc import Callable

from loguru import logger


def stability_testing(f: Callable, interval: float = 30, *args, **kwargs):
    """长稳测试

    :param f: 测试函数
    :param interval: 间隔时间
    :param args: 测试函数参数
    :param kwargs: 测试函数参数
    """
    try:
        i = 0
        logger.info(f"Starting stability testing, interval: {interval}s")
        while True:
            i += 1
            logger.info(f"Testing round {i}")
            f(*args, **kwargs)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")

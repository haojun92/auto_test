import functools

from pcan_ext.logger import logger
from PCANBasic import *  # noqa


def check_status(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        status: TPCANStatus = f(self, *args, **kwargs)
        if status == PCAN_ERROR_OK:
            logger.info(f"{f.__name__} success")
            return True
        logger.error(f"{f.__name__} failed, {status=}")
        _, msg = self.dll.GetErrorText(status, 0x09)  # 0x09: English
        logger.error(f"{f.__name__} failed, {msg=}")
        return False

    return wrapper

import time

from pcan_ext.callback import callback_rx_print
from pcan_ext.channel import Channel
from PCANBasic import *  # noqa

if __name__ == "__main__":
    ch = Channel()
    ch.initialize(channel_handle=PCAN_USBBUS2)

    thread = ch.threading_read_message([callback_rx_print])
    thread.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        ...

    thread.cancel()
    thread.join()

    ch.release()

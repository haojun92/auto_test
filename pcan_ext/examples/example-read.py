from pcan_ext.callback import callback_rx, callback_rx_print
from pcan_ext.channel import Channel
from pcan_ext.utils import Data
from PCANBasic import *  # noqa

if __name__ == "__main__":
    ch = Channel()
    ch.initialize(channel_handle=PCAN_USBBUS2)

    ch.read_messages(callbacks=[callback_rx_print, callback_rx])

    ch.release()

    print(f"{Data()=}")

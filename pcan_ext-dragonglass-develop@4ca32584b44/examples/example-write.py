import time

from pcan_ext.callback import callback_tx_print
from pcan_ext.channel import Channel
from PCANBasic import *  # noqa

if __name__ == "__main__":
    ch = Channel()
    ch.initialize(channel_handle=PCAN_USBBUS1)

    for i in range(5):
        ch.write_message(
            frame_id=0x49D,
            data=bytes([0, 0, 2, 0, 0, 0, 0, 0]),
            callbacks=[callback_tx_print],
        )
        ch.write_message(
            frame_id=0x600,
            data=bytes([0, 0, 0, 0, 0, 0, 0, 0]),
            callbacks=[callback_tx_print],
        )
        ...
        time.sleep(0.1)

    ch.release()

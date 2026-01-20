import time
from pathlib import Path

from pcan_ext.callback import callback_tx_print
from pcan_ext.channel import Channel
from pcan_ext.utils import DBC, Tx
from PCANBasic import *  # noqa

if __name__ == "__main__":
    dbc_path = "BEV_E0X_OT_Car ADCC_DA Message list  V3.60 Draft _202308301702.dbc"
    dbc = DBC(dbc_path=Path(__file__).parent / dbc_path)

    message = dbc.db.get_message_by_frame_id(0x49D)
    Tx().update({0x49D: dbc.encode(message, input_data={"FLZCU_9_PowerMode": 2})})
    Tx().update({0x600: bytes([0, 0, 0, 0, 0, 0, 0, 0])})

    ch = Channel()
    ch.initialize(channel_handle=PCAN_USBBUS1)

    threads = [
        ch.threading_write_message(
            interval=100,
            frame_id=0x49D,
            callbacks=[
                dbc.callback_crc8,
                callback_tx_print,
            ],
        ),
        ch.threading_write_message(
            interval=1000,
            frame_id=0x600,
            callbacks=[
                callback_tx_print,
            ],
        ),
    ]
    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        ...

    for thread in threads:
        thread.cancel()
    for thread in threads:
        thread.join()

    ch.release()

import time
import typing

from pcan_ext.constant import DLC_MAPPING
from pcan_ext.utils import Rx, Tx, msg_type2str
from PCANBasic import *  # noqa


# for rx
def callback_rx(
    status: TPCANStatus,
    timestamp: typing.Union[TPCANTimestamp, TPCANTimestampFD],
    msg: typing.Union[TPCANMsg, TPCANMsgFD],
) -> None:
    Rx()[msg.ID] = {
        "status": status,
        "timestamp": timestamp.value,
        "msg": {
            "ID": msg.ID,
            "MSGTYPE": msg.MSGTYPE,
            "DLC": msg.DLC,
            "DATA": bytes(msg.DATA[: DLC_MAPPING[msg.DLC]]),
        },
    }


def callback_print(direction: typing.Literal["Rx", "Tx"], frame_id: int, data: bytes) -> None:
    print(direction, f"{time.time():.7f}", f"0x{frame_id:03X}", data.hex(" ").upper())


def callback_rx_print(
    status: TPCANStatus,
    timestamp: typing.Union[TPCANTimestamp, TPCANTimestampFD],
    msg: typing.Union[TPCANMsg, TPCANMsgFD],
) -> None:
    frame_id = msg.ID
    data = bytes(msg.DATA[: DLC_MAPPING[msg.DLC]])
    callback_print("Rx", frame_id, data)


# for tx
def callback_tx(frame_id: int, data: bytes) -> typing.Tuple[int, bytes]:
    return frame_id, data or Tx()[frame_id]


def callback_tx_print(frame_id: int, data: bytes) -> typing.Tuple[int, bytes]:
    callback_print("Tx", frame_id, data)
    return frame_id, data

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
	

def callback_tx_qh01_crc8(
        frame_id: int,
        data: bytes,
    ) -> typing.Tuple[int, bytes]:
        if frame_id not in frame_ids:
            return frame_id, data

        origin_data = list(data)

        data_ids_info = self.get_data_ids_info(frame_id)
        self.cnts[frame_id] = self.cnts[frame_id] or [data_id_info["cnt"].minimum for data_id_info in data_ids_info]

        for index, data_id_info in enumerate(data_ids_info):
            signal_crc: database.Signal = data_id_info["crc"]
            signal_cnt: database.Signal = data_id_info["cnt"]
            cnt: int = self.cnts[frame_id][index]

            if signal_crc.byte_order == "big_endian":
                start: int = signal_crc.start >> 3

            # TODO: 此处假设了数据拼接方式为data_id+cnt+raw[2:]
            # TODO: 此处假设了crc算法为crc8
            _piece: typing.List[int] = [cnt, *data[start + 2 : start + 8]]
            check_sum: int = crc8(bytes([*data_id_info["data_id"].to_bytes(2)[::-1], *_piece]))

            origin_data[start] = check_sum
            origin_data[start + 1] = cnt

            self.cnts[frame_id][index] = (cnt + 1) % (signal_cnt.maximum + 1)

        return frame_id, bytes(origin_data)

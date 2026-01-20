import os
import re
import typing

try:
    from functools import cache
except ImportError:
    cache = lambda _: _


from functools import cached_property

from cantools import database

from pcan_ext.crc import crc8
from PCANBasic import *  # noqa


def msg_type2str(msg_type: int) -> str:
    types: typing.List[str] = []
    if msg_type == PCAN_MESSAGE_STANDARD.value:
        types.append("STANDARD")
    if msg_type & PCAN_MESSAGE_RTR.value:
        types.append("RTR")
    if msg_type & PCAN_MESSAGE_EXTENDED.value:
        types.append("EXTENDED")
    if msg_type & PCAN_MESSAGE_FD.value:
        types.append("FD")
    if msg_type & PCAN_MESSAGE_BRS.value:
        types.append("BRS")
    if msg_type & PCAN_MESSAGE_ESI.value:
        types.append("ESI")
    if msg_type & PCAN_MESSAGE_ECHO.value:
        types.append("ECHO")
    if msg_type & PCAN_MESSAGE_ERRFRAME.value:
        types.append("ERRFRAME")
    if msg_type & PCAN_MESSAGE_STATUS.value:
        types.append("STATUS")
    return " ".join(types) if types else hex(msg_type)


class Singleton(type):
    """
    example:
        Data1 = Singleton("Data1", (dict,), {})
        Data2 = Singleton("Data2", (dict,), {})
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


Rx = Singleton("Rx", (dict,), {})
Tx = Singleton("Tx", (dict,), {})


class DBC(object):
    def __init__(self, dbc_path: str):
        self.dbc_path = dbc_path
        self.db = database.load_file(dbc_path, encoding="GB2312", strict=False)

        self.cnts = {message.frame_id: [] for message in self.db.messages}

    @property
    def channel_name(self) -> str:
        return self.db.nodes[0].name

    @cached_property
    def frame_ids(self) -> typing.List[int]:
        return [message.frame_id for message in self.db.messages]

    @cache
    def get_data_ids_info(self, frame_id: int) -> typing.List[dict]:
        info: typing.List[dict] = []
        message = self.db.get_message_by_frame_id(frame_id)
        for signal in message.signals:
            if re.search(r".+_CRC(\d*)", signal.name):
                index: str = re.match(r".+_CRC(\d*)", signal.name)[1]  # '1'|'2'|...

                data_id = None  # NO ASIL requirements
                try:
                    data_id = int(re.search(r"0x[0-9A-F]+", signal.comment).group(), 16)
                except AttributeError:
                    if "Use CANID,other bits Fill with 0" in signal.comment:
                        data_id = message.frame_id

                cnt = [
                    signal
                    for signal in message.signals
                    if re.search(rf".+_(RollgCntr|RollingCounter){index}", signal.name)
                ][0]

                info.append(
                    {
                        "data_id": data_id,
                        "crc": signal,
                        "cnt": cnt,
                    }
                )
        return info

    def callback_crc8(
        self,
        frame_id: int,
        data: bytes,
    ) -> typing.Tuple[int, bytes]:
        if frame_id not in self.frame_ids:
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
            check_sum: int = crc8(bytes([*data_id_info["data_id"].to_bytes(2, byteorder="little"), *_piece]))

            origin_data[start] = check_sum
            origin_data[start + 1] = cnt

            self.cnts[frame_id][index] = (cnt + 1) % (signal_cnt.maximum + 1)

        return frame_id, bytes(origin_data)

    def message_default_value(
        self,
        message: database.Message,
    ) -> dict:
        default = {}
        for signal in message.signals:
            initial = signal.initial or 0
            scale = signal.scale or 0
            offset = signal.offset or 0
            default[signal.name] = initial * scale + offset
        return default

    def encode(
        self,
        message: database.Message,
        input_data: typing.Dict[str, typing.Union[int, float]] = None,
    ) -> bytes:
        default: dict = self.message_default_value(message)
        data = message.gather_signals({**default, **input_data})
        return message.encode(data)


class DH_DBC(DBC):
    @cache
    def get_data_ids_info(self, frame_id: int) -> typing.List[dict]:
        info: typing.List[dict] = []
        message = self.db.get_message_by_frame_id(frame_id)
        for signal in message.signals:
            if re.search(r".*?(Checksum|CheckSum)", signal.name):
                data_id = frame_id
                print("data_id", data_id)

                cnt = [
                    signal for signal in message.signals if re.search(rf".*?(RollingCount|RollingCounter)", signal.name)
                ][0]

                info.append(
                    {
                        "data_id": data_id,
                        "crc": signal,
                        "cnt": cnt,
                    }
                )
        return info

    def callback_crc8(
        self,
        frame_id: int,
        data: bytes,
    ) -> typing.Tuple[int, bytes]:
        if frame_id not in self.frame_ids:
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

            _piece: typing.List[int] = [*data[: start - 1], cnt]  # len: 11
            check_sum: int = crc8(bytes([*data_id_info["data_id"].to_bytes(2, byteorder="big"), *_piece]))

            origin_data[start] = check_sum
            origin_data[start - 1] = cnt

            self.cnts[frame_id][index] = (cnt + 1) % (2**signal_cnt.length)

        return frame_id, bytes(origin_data)

import json
import re
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path

import click
from cantools import database
from cantools.database import Database, Message
from loguru import logger
from pcan_ext.callbacks import callback_tx_qh01_crc8
from pcan_ext.pcan import PCan
from pcan_ext.typing import FrameID
from PCANBasic import PCAN_USBBUS2


def get_data_ids(dbc: Database, frame_id: FrameID) -> list[int]:
    """QH01 从DBC文件获取DataID"""
    out: list[int] = []
    message = dbc.get_message_by_frame_id(frame_id)
    for signal in message.signals:
        if re.search(r".+_CRC(\d*)", signal.name):
            data_id = None  # NO ASIL requirements
            try:
                data_id = int(re.search(r"0x[0-9A-F]+", signal.comment).group(), 16)
            except AttributeError:
                if "Use CANID,other bits Fill with 0" in signal.comment:
                    data_id = message.frame_id
            out.append(data_id)
    return out


def get_data(dbc_ch: str, data_file: str):
    dbc: Database = database.load_file(dbc_ch, encoding="GB2312", strict=False)
    data: dict = (
        json.loads(Path(data_file).read_text())
        if Path(data_file).exists()
        else {
            "ACU_2": {
                "ACU_2_YawrateSigValidData": 0,  # valid
                "ACU_2_YawRate": 0.0,
                "ACU_2_LateralAccelerationSigVD": 0,  # valid
                "ACU_2_LateralAcceleration": 0.0,
            },
            "ACU_3": {
                "ACU_3_LongitudinalAccelerationVD": 0,  # valid
                "ACU_3_LongitudinalAcceleration": 0.0,
            },
            "ONEBOX_1": {
                "ESP1_VehicleSpeedVSOSigValidData": 0,  # valid
                "ABS_ESP_1_VehicleSpeedVSOSig": 40,  # km/h
            },
            "SAS_1": {
                "SAM_1_SteeringAngleSpeed": 0,
                "SAM_1_SteeringAngleSpeedVD": 0,  # valid
                "SAM_1_SteeringAngle": 0,
                "SAM_1_SteeringAngleVD": 0,  # valid
            },
            "VCU_COM_10": {
                # "VCU_ActualGear": 0x1,  # P档
                # "VCU_ActualGear": 0x2,  # R档
                # "VCU_ActualGear": 0x3,  # N档
                "VCU_ActualGear": 0x4,  # D档
                "VCU_ActualGearValidData": 1,  # valid
            },
        }
    )
    for message_name, signals in data.items():
        message: Message = dbc.get_message_by_name(name=message_name)
        # frame_id
        frame_id: FrameID = FrameID(message.frame_id)
        # interval
        interval: int = message.cycle_time
        # data
        default: dict[str, int | float] = {}
        for signal in message.signals:
            initial = signal.raw_initial or 0
            scale = signal.scale or 0
            offset = signal.offset or 0
            default[signal.name] = initial * scale + offset
        data: dict = message.gather_signals({**default, **signals})
        data: bytes = message.encode(data)
        # data_ids
        data_ids: list = get_data_ids(dbc, FrameID(frame_id))
        # callbacks
        callbacks: list[Callable] = [
            partial(callback_tx_qh01_crc8, data_ids=data_ids),
            # callback_tx_print,
        ]
        yield frame_id, {"interval": interval, "data": data, "callbacks": callbacks}


def main(dbc_ch: str, data_file: str):
    logger.enable("pcan_ext")

    can2 = PCan().add_network(handle=PCAN_USBBUS2, is_fd=True)
    # PCan()[can2].rx["callbacks"] = [callback_rx_print]
    for frame_id, tx_data in get_data(dbc_ch, data_file):
        PCan()[can2].tx[frame_id] = tx_data

    PCan().start_all()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.warning("Ctrl+C pressed")
    finally:
        PCan().stop_all()


@click.command()
@click.option(
    "--dbc-ch",
    type=click.Path(exists=True),
    required=True,
    help="ADCC CH CAN DBC文件路径",
    default=r"C:\Users\jianghui\workspaces\QH01\dbc\ADCC 3.6.0\BEV_E0X_OT_Car ADCC_CH Message list  V3.60 Draft _202308301702.dbc",  # noqa: E501
)
@click.option(
    "--data-file",
    type=str,
    help="ADCC CH CAN 数据文件路径",
    default="ch.json",
)
def cli(dbc_ch: str, data_file: str) -> None:
    """CH CAN基础消息模拟"""
    main(dbc_ch=dbc_ch, data_file=data_file)


if __name__ == "__main__":
    cli()

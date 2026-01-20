import json
import sys
import time
from collections.abc import Callable

import click
from cantools import database
from cantools.database import Database, Message
from loguru import logger
from pcan_ext.callbacks import callback_tx_dh01_0x4DA, callback_tx_dh01_crc8
from pcan_ext.pcan import PCan
from pcan_ext.typing import FrameID
from PCANBasic import PCAN_USBBUS1


def main():
    logger.enable("pcan_ext")
    logger.remove(0)
    logger.add(sys.stderr, level="INFO")

    can1 = PCan().add_network(handle=PCAN_USBBUS1, is_fd=True)
    # PCan()[can1].rx["callbacks"] = [callback_rx, callback_rx_print]
    PCan()[can1].tx[FrameID(0x4DA)] = {
        "interval": 1000,
        "data": bytes([0, 0, 0, 0, 0, 0, 0, 0]),
        "callbacks": [callback_tx_dh01_0x4DA],
    }

    PCan().start_all()
    dbc: Database = database.load_file(
        r"C:\Users\jianghui\workspaces\DH01\dbc\DH_CA_3_1.dbc",
        encoding="GB2312",
        strict=False,
    )
    try:
        while True:
            time.sleep(1)
            try:
                with open("ca.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(e)
            else:
                try:
                    for message_name, signals in data.items():
                        message: Message = dbc.get_message_by_name(name=message_name)
                        # frame_id
                        frame_id: FrameID = FrameID(message.frame_id)
                        # data
                        default: dict[str, int | float] = {}
                        for signal in message.signals:
                            initial = signal.raw_initial or 0
                            scale = signal.scale or 0
                            offset = signal.offset or 0
                            default[signal.name] = initial * scale + offset
                        data: dict = message.gather_signals({**default, **signals})
                        data: bytes = message.encode(data)
                        if frame_id in PCan()[can1].tx:
                            PCan()[can1].tx[frame_id]["data"] = data
                            continue
                        # interval
                        interval: int = message.cycle_time
                        # callbacks
                        callbacks: list[Callable] = []
                        if message.name in [
                            # "Camera_C_CA",
                            "IBC7_CA",
                            "ACU_YRS_119_CA",
                            "TAS_Info_CA",
                            "PDCM10_CA",
                        ]:
                            callbacks: list[Callable] = [callback_tx_dh01_crc8]
                        PCan()[can1].tx[frame_id] = {"interval": interval, "data": data, "callbacks": callbacks}
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(e)
    except KeyboardInterrupt:
        logger.warning("Ctrl+C pressed")
    finally:
        PCan().stop_all()


@click.command()
def cli() -> None:
    """NM激活工具"""
    main()


if __name__ == "__main__":
    cli()

import logging
import re
from functools import partial
from math import ceil
from typing import Literal

import can
import requests
from isotp import Address, CanStack
from loguru import logger
from udsoncan import ClientConfig, MemoryLocation, services, setup_logging
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection


class InterceptHandler(logging.Handler):
    def emit(self, record):
        opt = logger.opt(depth=6, exception=record.exc_info)
        opt.log(logger.level(record.levelname).name, record.getMessage())


def security_algo(level, seed, params, project: Literal["qh01", "qh01/adcc", "qh01/fcm", "dh01"]):  # noqa
    return bytes.fromhex(requests.get(f"http://10.5.0.12:8000/{project}/{seed.hex()}").json()["data"])


class DoCAN:
    config: ClientConfig = {
        "security_algo": partial(security_algo, project="dh01"),
        "use_server_timing": False,
        "p2_timeout": 10.1,
        "p2_star_timeout": 5.05,
        "data_identifiers": {
            0xD124: "7s",
            0xF179: "2s",
            0xF184: "9s",
            0xF187: "14s",
            0xF188: "14s",
            0xF189: "2s",
            0xF18C: "20s",
            0xF191: "14s",
        },
    }

    def __init__(self) -> None:
        setup_logging()
        for name in ["UdsClient", "Connection"]:
            if name not in logging.root.manager.loggerDict:
                continue
            logging.getLogger(name).setLevel("DEBUG")
            logging.getLogger(name).handlers = []
            logging.getLogger(name).addHandler(InterceptHandler())

        conn = PythonIsoTpConnection(
            CanStack(
                bus=can.interface.Bus(
                    bustype="pcan",
                    fd=True,
                    f_clock=80000000,
                    nom_brp=4,
                    nom_tseg1=31,
                    nom_tseg2=8,
                    nom_sjw=8,
                    data_brp=4,
                    data_tseg1=6,
                    data_tseg2=3,
                    data_sjw=3,
                ),
                address=Address(txid=0x734, rxid=0x73C, physical_id=0x734, functional_id=0x7DF),
                params={
                    "stmin": 5,
                    # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
                    "blocksize": 0,  # Request the sender to send 8 consecutives frames before sending a new flow control message
                    "wftmax": 0,  # Number of wait frame allowed before triggering an error
                    "tx_data_length": 8,  # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
                    "tx_data_min_length": None,
                    # Minimum length of CAN messages. When different from None, messages are padded to meet this length. Works with CAN 2.0 and CAN FD.
                    "tx_padding": 0xCC,  # Will pad all transmitted CAN messages with byte 0x00.
                    "rx_flowcontrol_timeout": 1000,  # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
                    "rx_consecutive_frame_timeout": 1000,
                    # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
                    # "squash_stmin_requirement": False,
                    # When sending, respect the stmin requirement of the receiver. If set to True, go as fast as possible.
                    "max_frame_size": 4095,  # Limit the size of receive frame.
                    "bitrate_switch": True,
                    "can_fd": True,
                },
            )
        )
        self.client = Client(conn=conn, config=self.config, request_timeout=300.0)
        self.client.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def hard_reset(self):
        self.client.ecu_reset(services.ECUReset.ResetType.hardReset)

    @staticmethod
    def read_dtc(raw: bytes, size: int = 4) -> list[bytes]:
        return list(map(lambda x: raw[x * size : x * size + size], list(range(0, ceil(len(raw) / size)))))  # noqa: E203

    def _transfer_data(self, data: str):
        d: list[str] = re.findall(r"\w{4096}", data)
        d[-1] = (d[-1] + "0" * 4096)[:4096]
        for index, raw in enumerate(d):
            self.client.transfer_data((index + 1) % 0x100, bytes.fromhex(raw))  # 36 01

    def flash(self, mem_address: int, mem_size: int, hex_str: str, hex_crc: bytes):
        """

        Parameters
        ----------
        mem_address: 内存地址
        mem_size: 内存长度
        hex_str: 刷写数据内容
        hex_crc: 刷写数据内容CRC值

        Returns
        -------

        """
        self.client.request_download(
            memory_location=MemoryLocation(mem_address, mem_size, address_format=32, memorysize_format=32)
        )  # 34 00 44
        self._transfer_data(data=hex_str)  # 36 01
        self.client.()  # 37

        response = self.client.routine_control(
            0x02_02,
            services.RoutineControl.ControlType.startRoutine,
            data=mem_address.to_bytes(length=4) + mem_size.to_bytes(length=4) + hex_crc,
        )  # 31 01 02 02
        if response.service_data.routine_id_echo >> 16 == 0x01:
            # 0x00:校验成功
            # 0x01:校验失败
            raise RuntimeError("Check memory failed")
request_transfer_exit
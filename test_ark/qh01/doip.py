import logging
import os
from functools import partial
from math import ceil
from typing import Any, Literal
from pathlib import Path
import requests
import udsoncan
from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from loguru import logger
from udsoncan.client import Client
from udsoncan.services import ECUReset
# from encryption import Generator


class InterceptHandler(logging.Handler):
    def emit(self, record):
        opt = logger.opt(depth=6, exception=record.exc_info)
        opt.log(logger.level(record.levelname).name, record.getMessage())


for name in ["doipclient", "UdsClient", "Connection"]:
    if name not in logging.root.manager.loggerDict:
        continue
    logging.getLogger(name).setLevel("DEBUG")
    logging.getLogger(name).handlers = []
    logging.getLogger(name).addHandler(InterceptHandler())


class AsciiCodec0xF184(udsoncan.AsciiCodec):
    def decode(self, string_bin: bytes) -> Any:
        date = "".join(f"{i:02d}" for i in string_bin[:3])
        serial_number = "".join(chr(i) for i in string_bin[3:])
        return f"{date} {serial_number}"


class UnSignedCodec(udsoncan.AsciiCodec):
    def decode(self, string_bin: bytes) -> int:
        return int.from_bytes(string_bin, byteorder="big", signed=False)


class Codec0xF0F2(udsoncan.AsciiCodec):
    def decode(self, string_bin: bytes) -> str:
        """
        Byte1：
        0x00:success
        0x01:failure
        0x02: installing
        0x03:being verified
        0x04: installation fails
        0x05:verification fails
        0x06-0xFF:Reserved

        Byte2：
        0x00-0x64，百分比进度
        """
        mapping = {
            0x00: "success",
            0x01: "failure",
            0x02: "installing",
            0x03: "being verified",
            0x04: "installation fails",
            0x05: "verification fails",
            0x06: "Reserved",
            0xFF: "Reserved",
        }
        state: str = mapping.get(string_bin[0], "Reserved")
        progress: int = string_bin[1]
        return f"{state} {progress}"


class Codec0xF18B(udsoncan.AsciiCodec):
    def decode(self, string_bin: bytes) -> str:
        """
        Byte1：Year high，取值范围00-99
        Byte2：Year low，取值范围00-99
        Byte3：Month，取值范围00-99
        Byte4：Day，取值范围00-99
        """
        return "".join(f"{i:02d}" for i in string_bin)


class NoExceptionAsciiCodec(udsoncan.AsciiCodec):
    def decode(self, string_bin: bytes) -> Any:
        try:
            return super().decode(string_bin)
        except UnicodeDecodeError:
            return string_bin


# def security_algo(level, seed, params, project: Literal["qh01", "qh01/adcc", "qh01/fcm", "dh01"]):  # noqa
#     return bytes.fromhex(requests.get(f"http://10.5.0.12:8000/{project}/{seed.hex()}").json()["data"])



def security_algo(level, seed):  # noqa
    # return bytes.fromhex(requests.get(f"http://10.5.0.12:8000/{project}/{seed.hex()}").json()["data"])
    return Generator((Path() / "IDCU_Vector.dll").absolute().as_posix()).request_key(str(seed))


class DoIP:
    config: udsoncan.ClientConfig = {
        "security_algo": security_algo,
        "data_identifiers": {
            # 版本信息
            0xF013: NoExceptionAsciiCodec(16),
            0xF089: NoExceptionAsciiCodec(24),
            0xF0F0: NoExceptionAsciiCodec(1),
            0xF0F1: UnSignedCodec(4),
            0xF0F2: Codec0xF0F2(2),
            0xF0F3: UnSignedCodec(4),
            0xF180: NoExceptionAsciiCodec(32),
            0xF184: AsciiCodec0xF184(19),
            0xF186: UnSignedCodec(1),
            0xF187: NoExceptionAsciiCodec(16),
            0xF189: NoExceptionAsciiCodec(24),
            0xF18A: NoExceptionAsciiCodec(10),
            0xF18B: Codec0xF18B(4),
            0xF18C: NoExceptionAsciiCodec(36),
            0xF190: NoExceptionAsciiCodec(17),
            0xF195: NoExceptionAsciiCodec(9),
            # 0xF289: NoExceptionAsciiCodec(38),
            0xF289: NoExceptionAsciiCodec(29),
            # 0xF289: NoExceptionAsciiCodec(29),
            # DID列表
            0x4000: NoExceptionAsciiCodec(4),
            0x4080: NoExceptionAsciiCodec(4),
            0x4001: NoExceptionAsciiCodec(1),
            0x4002: NoExceptionAsciiCodec(2),
            0x4003: NoExceptionAsciiCodec(3),
            0x4004: NoExceptionAsciiCodec(6),
            0x4005: NoExceptionAsciiCodec(1),
            0x4006: NoExceptionAsciiCodec(2),
            0x4007: NoExceptionAsciiCodec(192),
            0xF011: "900s",
            0x4008: NoExceptionAsciiCodec(1),
            0x4009: NoExceptionAsciiCodec(6),
            0x400A: NoExceptionAsciiCodec(4),
            0x400B: NoExceptionAsciiCodec(6),
            0x400C: NoExceptionAsciiCodec(1),
            0x4010: NoExceptionAsciiCodec(10),
            0x4011: NoExceptionAsciiCodec(1),
            0x4013: NoExceptionAsciiCodec(1),
            0x4014: NoExceptionAsciiCodec(1),
            # 0x4014: NoExceptionAsciiCodec(4),
            0x4015: NoExceptionAsciiCodec(1),
            0x40A3: NoExceptionAsciiCodec(5),
            0x40A4: NoExceptionAsciiCodec(32),
            0x40A6: NoExceptionAsciiCodec(40),
            0x40A7: NoExceptionAsciiCodec(9),
            0x40AB: NoExceptionAsciiCodec(8),
            0x40AC: NoExceptionAsciiCodec(16),
            0x40AD: NoExceptionAsciiCodec(16),
            0x4017: NoExceptionAsciiCodec(67),
            0x4018: NoExceptionAsciiCodec(59),
            0x4020: NoExceptionAsciiCodec(20),
            0x4021: NoExceptionAsciiCodec(13),
            0xF020: NoExceptionAsciiCodec(1),
        },
        "use_server_timing": False,
        "p2_timeout": 10,
    }

    def __init__(
        self,
        ecu_ip_address: str = os.getenv("IP_QH01_TDA4", "192.168.69.15"),
        protocol_version: int = 0x03,
        ecu_logical_address: int = 0x07c0,
        client_logical_address: int = 0x0E80,
    ) -> None:
        doip_layer = DoIPClient(
            ecu_ip_address,
            ecu_logical_address,
            protocol_version=protocol_version,
            client_logical_address=client_logical_address,
        )
        conn = DoIPClientUDSConnector(doip_layer, close_connection=True)

        self.client = Client(conn=conn, config=self.config, request_timeout=300.0)
        self.client.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def hard_reset(self):
        self.client.ecu_reset(ECUReset.ResetType.hardReset)

    @staticmethod
    def read_dtc(raw: bytes, size: int = 4) -> list[bytes]:
        return list(map(lambda x: raw[x * size : x * size + size], list(range(0, ceil(len(raw) / size)))))  # noqa: E203


if __name__ == '__main__':
    DoIP().hard_reset()
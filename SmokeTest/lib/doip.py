import logging
import os
import re
from functools import partial
from math import ceil
from typing import Any, Literal
from pathlib import Path
import requests
import udsoncan
from charset_normalizer import from_bytes
from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from loguru import logger
from udsoncan.client import Client
from udsoncan.services import ECUReset
#from encryption import Generator
import subprocess
import sys


class InterceptHandler(logging.Handler):
    def emit(self, record):
        opt = logger.opt(depth=6, exception=record.exc_info)
        opt.log(logger.level(record.levelname).name, record.getMessage())


# for name in ["doipclient", "UdsClient", "Connection"]:
#     if name not in logging.root.manager.loggerDict:
#         continue
#     # logging.getLogger(name).setLevel("ERROR")
#     logging.getLogger(name).setLevel("DEBUG")
#     logging.getLogger(name).handlers = []
#     logging.getLogger(name).addHandler(InterceptHandler())


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

class CodecHex(udsoncan.AsciiCodec):
    def encode(self, string_ascii: Any) -> bytes:
        return bytes.fromhex(string_ascii)

    def decode(self, string_ascii: Any) -> Any:
        return str(string_ascii)



# def security_algo(level, seed):  # noqa
#     t = requests.get(f"http://127.0.0.1:8000/{seed.hex()}").json()["data"]
#     # return bytes.fromhex(requests.get(f"http://127.0.0.1:8000/{seed.hex()}").json()["data"])
#     return bytes(t)


def security_algo(level, seed):  # noqa
    # return bytes.fromhex(requests.get(f"http://10.5.0.12:8000/{project}/{seed.hex()}").json()["data"])
    # return Generator((Path() / "E0X_FCM.dll").absolute().as_posix()).request_key(seed.hex())
    level = hex(level)[2:].zfill(2)
    seed = ''.join(hex(seed[i])[2:].zfill(2) for i in range(16))
    # print(level)
    # print(seed)
    process = subprocess.Popen(['c:\Program Files (x86)\Python39-32\python.exe', 'lib\encryption.py', seed, level], stdout=subprocess.PIPE)
    output, error = process.communicate()  # 获取输出和错误信息
    key = output.decode().strip()
    key_list = []
    for i in range(16):
        key_list.append(int(key[i*2:i*2+2],16))

    return bytes(key_list)


class DoIP:
    config: udsoncan.ClientConfig = {
        "security_algo": security_algo,
        "data_identifiers": {
            # 版本信息
            0xF013: NoExceptionAsciiCodec(16),
            0xF15A: AsciiCodec0xF184(15),
            0xF022: CodecHex(514),
            0xF021: CodecHex(514),
            0xF190: CodecHex(17),
            0xF191: NoExceptionAsciiCodec(5),
            0xF15B: NoExceptionAsciiCodec(15),
            0xF089: NoExceptionAsciiCodec(24),
            0xF0F0: NoExceptionAsciiCodec(1),
            0xF0F1: UnSignedCodec(4),
            0xF0F2: Codec0xF0F2(2),
            0xF0F3: UnSignedCodec(4),
            0xF180: NoExceptionAsciiCodec(32),
            0xF031: NoExceptionAsciiCodec(16),
            0xF032: NoExceptionAsciiCodec(24),
            0xF184: AsciiCodec0xF184(19),
            0xF189: AsciiCodec0xF184(24),
            0xF186: UnSignedCodec(1),
            0xF187: NoExceptionAsciiCodec(16),
            0xF188: NoExceptionAsciiCodec(8),
            0xF18A: NoExceptionAsciiCodec(10),
            0xF18B: Codec0xF18B(4),
            0xF18C: NoExceptionAsciiCodec(36),
            0xF195: NoExceptionAsciiCodec(9),
            0xF091: NoExceptionAsciiCodec(246),
            0xF160: NoExceptionAsciiCodec(1),
            0xF193: NoExceptionAsciiCodec(9),
            # DID列表
            0x4700: NoExceptionAsciiCodec(4),
            0x4780: NoExceptionAsciiCodec(4),
            0x4701: NoExceptionAsciiCodec(1),
            0x4702: NoExceptionAsciiCodec(2),
            0x4703: NoExceptionAsciiCodec(3),
            0x4704: NoExceptionAsciiCodec(6),
            0x4005: NoExceptionAsciiCodec(1),
            0x4006: NoExceptionAsciiCodec(2),
            0x4707: NoExceptionAsciiCodec(15),
            # 0xF011: "900s",
            0x4708: NoExceptionAsciiCodec(1),
            # 0x4009: NoExceptionAsciiCodec(6),
            0x470A: NoExceptionAsciiCodec(1),
            0x470B: NoExceptionAsciiCodec(4),
            0x470D: NoExceptionAsciiCodec(1),
            0x470E: NoExceptionAsciiCodec(20),
            0x470F: NoExceptionAsciiCodec(3),
            0x4710: NoExceptionAsciiCodec(1),
            0x4711: NoExceptionAsciiCodec(1),
            0x4713: NoExceptionAsciiCodec(1),
            0x4714: NoExceptionAsciiCodec(6),
            0x4715: NoExceptionAsciiCodec(40),
            0x4717: NoExceptionAsciiCodec(1),
            0x4716: NoExceptionAsciiCodec(1),
            0x4718: NoExceptionAsciiCodec(24),
            0x4725: NoExceptionAsciiCodec(1146),
            0x4726: NoExceptionAsciiCodec(2666),
            0x4727: NoExceptionAsciiCodec(2666),
            0x4728: NoExceptionAsciiCodec(766),
            0x4729: NoExceptionAsciiCodec(766),
            0x472A: NoExceptionAsciiCodec(9),
            0xF161: NoExceptionAsciiCodec(160),
            0xF020: NoExceptionAsciiCodec(1),
        },
        "use_server_timing": False,
        "p2_timeout": 30,
        # "suppress_positive_response": True,
    }

    def __init__(
        self,
        ecu_ip_address: str = os.getenv("E01", "192.168.69.15"),
        protocol_version: int = 0x03,
        ecu_logical_address: int = 0x0410,
        ecu_functional_address: int = 0xE400,
        client_logical_address: int = 0xE80,
    ) -> None:
        doip_layer = DoIPClient(
            ecu_ip_address,
            ecu_logical_address,
            protocol_version=protocol_version,
            client_logical_address=client_logical_address,
        )
        conn = DoIPClientUDSConnector(doip_layer, close_connection=True)

        self.client = Client(conn=conn, config=self.config, request_timeout=500.0)
        self.client.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def hard_reset(self):
        self.client.ecu_reset(ECUReset.ResetType.hardReset)

    #@staticmethod
    #def read_dtc(raw: bytes, size: int = 4) -> list[bytes]:
    #    return list(map(lambda x: raw[x * size : x * size + size], list(range(0, ceil(len(raw) / size)))))  # noqa: E203

    def transfer_data_service(self,file_path):
        # 假设的最大数据块大小
        chunk_size = 262142
        # chunk_size = 400000
        index = 1
        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    # data = bytearray([0x36, index]) + bytearray(chunk)
                    data = bytearray(chunk)
                    # 这里假设你有一个发送数据的函数，需要根据实际情况实现
                    self.client.transfer_data(index,bytes(data))
                    index += 1
                    if index > 255:
                        index = 0
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在。")



if __name__ == '__main__':
    doip = DoIP()
    doip.client.change_session(0x03)
    doip.client.start_routine(0x0203)
    # print(doip.client.change_session(0x02).get_payload().hex())
    # print(doip.client.communication_control(0x03,0x03).get_payload().hex())
    # print(doip.client.communication_control(0x00,0x03).get_payload().hex())
    # print(doip.client.request_seed(0x03))
    # print(doip.client.send_key(0x04,bytes(0x0,0x0,0x0,0x0)))
    doip.client.unlock_security_access(0x01)
    doip.client.write_data_by_identifier(0xF190,"0101010101010101010101010101010101")
    doip.client.read_data_by_identifier(0xF190)
    doip.client.write_data_by_identifier(0xF190,"0202020202020202020202020202020202")
    doip.client.read_data_by_identifier(0xF190)
    
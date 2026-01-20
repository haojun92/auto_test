import binascii
import time
from pathlib import Path

import click
from loguru import logger
from udsoncan import services

from test_ark.dh01.docan import DoCAN
from test_ark.qh01.stress import stress_testing


def main(s19_file: str, hex_file: str, *args, **kwargs):  # noqa
    s19_str = "".join([line[12:-3] for line in Path(s19_file).open(mode="r").readlines()[1:-1]])
    s19_crc = (binascii.crc32(bytes.fromhex(s19_str)) & 0xFFFFFFFF).to_bytes(length=4)  # [0xEC, 0x4A, 0x53, 0xD3]
    hex_str = "".join([line.strip()[9:-2] for line in Path(hex_file).open("r").readlines() if line.startswith(":20")])
    hex_crc = (binascii.crc32(bytes.fromhex(hex_str)) & 0xFFFFFFFF).to_bytes(length=4)  # [0xC2, 0x4A, 0x01, 0x3A]

    with DoCAN() as docan:
        # 刷写准备
        docan.client.change_session(services.DiagnosticSessionControl.Session.extendedDiagnosticSession)  # 10 03
        response = docan.client.routine_control(
            0x02_03, services.RoutineControl.ControlType.startRoutine
        )  # 31 01 02 03
        if response.service_data.routine_id_echo >> 16 == 0x01:
            raise RuntimeError("Condition not satisfied")
        docan.client.control_dtc_setting(services.ControlDTCSetting.SettingType.off)  # 85 02
        docan.client.communication_control(0x03, 0x03)  # 28 03 03
        docan.client.change_session(services.DiagnosticSessionControl.Session.programmingSession)  # 10 02
        docan.client.unlock_security_access(0x11)  # 27 11
        docan.client.write_data_by_identifier(
            0xF1_84, bytes([0x12, 0x12, 0x14, 0x32, 0x33, 0x34, 0x35, 0x37, 0x38])
        )  # 2E F1 84

        # 刷写驱动
        # -> XX XX XX XX -> 0x70, 0x10, 0x00, 0x00
        # -> YY YY YY YY -> 0x00, 0x00, 0x60, 0x00
        docan.flash(
            mem_address=int(bytes([0x70, 0x10, 0x00, 0x00]).hex(), 16),
            mem_size=int(bytes([0x00, 0x00, 0x60, 0x00]).hex(), 16),
            hex_str=s19_str,
            hex_crc=s19_crc,
        )

        # 刷写APP
        # -> XX XX XX XX -> 0x80, 0x08, 0x00, 0x00
        # -> YY YY YY YY -> 0x00, 0x38, 0x00, 0x00
        docan.client.routine_control(
            0xFF_00,
            services.RoutineControl.ControlType.startRoutine,
            data=bytes([0x80, 0x08, 0x00, 0x00, 0x00, 0x38, 0x00, 0x00]),
        )  # 31 01 FF 00
        # 31 01 FF 00的YY地址与34 00 44的YY地址不一致，原因是31 01 FF 00负责擦除，范围更大，34 00 44负责刷写，范围小。
        # 因此后续31 01 02 02的内存地址也是跟34 00 44一致的。
        # -> XX XX XX XX -> 0x80, 0x08, 0x00, 0x00
        # -> YY YY YY YY -> 0x00, 0x37, 0xC0, 0x00
        docan.flash(
            mem_address=int(bytes([0x80, 0x08, 0x00, 0x00]).hex(), 16),
            mem_size=int(bytes([0x00, 0x37, 0xC0, 0x00]).hex(), 16),
            hex_str=hex_str,
            hex_crc=hex_crc,
        )

        # 控制器回复
        docan.client.routine_control(0xFF_01, services.RoutineControl.ControlType.startRoutine)  # 31 01 FF 01
        docan.hard_reset()  # 11 01
        time.sleep(2)  # 等待2s，等11 01复位完成
        docan.client.change_session(services.DiagnosticSessionControl.Session.extendedDiagnosticSession)  # 10 03
        docan.client.communication_control(0x00, 0x03)  # 28 00 03
        docan.client.control_dtc_setting(0x01)  # 85 01
        docan.client.change_session(services.DiagnosticSessionControl.Session.defaultSession)  # 10 01


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=60, help="测试时间间隔")
@click.option("--s19-file", type=click.Path(exists=True), help="s19 文件路径")
@click.option("--hex-file", type=click.Path(exists=True), help="hex 文件路径")
def cli(count: int, interval: int, s19_file: str, hex_file: str):
    """压力测试-OTA"""
    logger.info("https://holomatic.feishu.cn/sheets/SvxBsl8eHhIl4Ot21CscD1Mtnnb?sheet=16TGVC")
    stress_testing(main, count=count, interval=interval, s19_file=s19_file, hex_file=hex_file)


if __name__ == "__main__":
    cli()

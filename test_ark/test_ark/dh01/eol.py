import time

import click
from loguru import logger
from udsoncan.services import ReadDataByIdentifier, ReadDTCInformation, RoutineControl

from test_ark.dh01.docan import DoCAN
from test_ark.dh01.fillback import FillBack
from test_ark.qh01.ssh import J3A
from test_ark.qh01.stress import stress_testing


def eol_calibration():
    """产线标定流程"""
    with DoCAN() as docan:
        docan.client.change_session(3)
        docan.client.unlock_security_access(0x1)
        docan.client.read_data_by_identifier(0xF187)
        docan.client.read_data_by_identifier(0xF188)
        docan.client.read_data_by_identifier(0xF189)
        docan.client.read_data_by_identifier(0xF191)
        docan.client.read_data_by_identifier(0xF179)
        docan.client.read_data_by_identifier(0xF18C)
        docan.client.clear_dtc()

        response = docan.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        if response.get_payload().hex() != "59028955420009" or "590289":
            logger.info("have other dtc code")

        docan.client.routine_control(0xFE01, RoutineControl.ControlType.startRoutine)  # 开始标定
        while True:  # 查询标定结果
            response: RoutineControl.InterpretedResponse = docan.client.routine_control(
                0xFE01, RoutineControl.ControlType.requestRoutineResults
            )
            if response.service_data.routine_status_record.hex() == "01":
                logger.info("Calibration running")
                time.sleep(3)
                continue
            elif response.service_data.routine_status_record.hex() == "02":
                logger.info("Calibration finished")
                break
            elif response.service_data.routine_status_record.hex() == "03":
                logger.error("Calibration failed")
                break

        d124: ReadDataByIdentifier.InterpretedResponse = docan.client.read_data_by_identifier(0xD124)  # 查询标定参数和失败原因
        if "62d12400" in d124.get_payload().hex():
            logger.info("eol success")
        else:
            logger.error(f"{d124.get_payload().hex()}")
        docan.client.clear_dtc()

        response = docan.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, 0x09)
        for index, dtc in enumerate(docan.read_dtc(response.data[2:])):
            logger.warning(f"DTC{index}: {dtc.hex()}")
            if dtc[-1] == 0x09 and dtc[:-1].hex() == "554200":
                raise Exception("故障状态，请检查！")

        docan.hard_reset()


def main(fillback_exec_path, fillback_pack_path, current: int = 1, *args, **kwargs):  # noqa
    # prepare
    FillBack.stop()
    with J3A() as ssh:
        ssh.exec_command("rm -rf /userdata/*.nv12")

    # fillback
    with FillBack(
        log_file=f"logs/{current}.fillback.log",
        fillback_exec_path=fillback_exec_path,
        fillback_pack_path=fillback_pack_path,
    ):
        time.sleep(30)  # 等待回灌程序正常输出图像

        logger.info("Start calibration")
        eol_calibration()


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=60, help="测试时间间隔")
@click.option("--fillback-exec-path", type=click.Path(exists=True), default="../tools/fillback/", help="回灌程序文件路径")
@click.option("--fillback-pack-path", type=click.Path(exists=True), default="./pack/", help="回灌pack文件路径")
def cli(count: int, interval: int, fillback_exec_path: str, fillback_pack_path: str):
    """压力测试-EOL标定"""
    logger.info("https://holomatic.feishu.cn/docx/ZxJed1UaIog4EexncpLcEa6snib")
    stress_testing(
        main,
        count=count,
        interval=interval,
        fillback_exec_path=fillback_exec_path,
        fillback_pack_path=fillback_pack_path,
    )


if __name__ == "__main__":
    cli()

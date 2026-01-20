import pytest
from udsoncan import services
from udsclient import UdsClient
from loguru import logger
import time
import allure
import json
import os
import logging
from subprocess import Popen


def update_json_value(file_path, key_to_update, new_value):
    # 读取 JSON 文件
    with open(file_path, 'r') as file1:
        data = json.load(file1)
    file1.close()
    # 修改指定键的值
    data['Fillback'][key_to_update] = new_value

    # 将修改后的数据写回 JSON 文件
    with open(file_path, 'w') as file2:
        json.dump(data, file2, indent=4, ensure_ascii=True)  # indent参数用于美化输出，可选
    file2.close()


def start_fill_back():
    fillback_type = 'bolepack'
    exe_type = 'bolepack.exe'
    global_type = 'fglobal.json'
    send_tool_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'auto_fillback', fillback_type))
    send_exe_path = os.path.join(send_tool_path, exe_type)
    calib_pack_addr = os.path.abspath(os.path.join(os.path.dirname(__file__), 'auto_fillback', "pack", "1"))

    send_global_json = os.path.join(send_tool_path, 'config', global_type)
    update_json_value(send_global_json, 'file_paths', [calib_pack_addr.replace("/", "\\")])

    command = f'cd {send_tool_path} & {send_exe_path} -fillback {send_global_json}'
    print(command)
    Popen(command, shell=True, creationflags=0x08000000)
    # print("回灌的进程在后台启动，需要执行kill_fill_back.py脚本或者在cmd执行: taskkill /F /IM bolepack.exe")


def kill_fill_back():
    Popen('taskkill /F /IM bolepack.exe', shell=True, creationflags=0x08000000)


def to_ascii(h):
    list_s = []
    for i in range(0, len(h), 2):
        list_s.append(chr(int(h[i:i + 2], 16)))
    return ''.join(list_s)


d = to_ascii('C')


def eol():
    with UdsClient() as uds:
        uds.client.change_session(0x60)
        uds.client.unlock_security_access(0x71)
        logger.info('unlock ecu success....')
        logging.info('unlock ecu success....')
        data = None
        data = uds.client.read_data_by_identifier(0xFD55)
        logger.info('读取外参完成')

        if res := uds.client.read_data_by_identifier(0xFD01):
            print(res.get_payload().hex())

            logger.info(f'Cali_Step:{res.get_payload().hex()[4:6]}')
            logger.info(f'SocSysSt:{res.get_payload().hex()[6:8]}')
            logger.info(f'Self_Cali_cnt:{res.get_payload().hex()[9:11]}')
            logger.info(f'cali_err_point:{res.get_payload().hex()[12:14]}')
        else:
            logger.info('读取FD01失败')

        uds.client.change_session(3)
        uds.client.unlock_security_access(1)
        uds.client.write_data_by_identifier(0xF190, '00000000000012345')
        uds.client.read_data_by_identifier(0xF190)
        time.sleep(0.1)
        logger.info('read vin code success')
        uds.client.read_data_by_identifier(0xF188)
        logger.info('read version success')
        uds.client.clear_dtc()
        uds.client.read_dtc_information(2, 9)
        uds.client.write_data_by_identifier(0x3BAF, f'{d}!')
        logger.info('写入校准距离成功')
        if res := uds.client.read_data_by_identifier(0x3BAF):
            print(res.data)

        uds.client.routine_control(0x03_A5, services.RoutineControl.ControlType.startRoutine)
        logger.info("开始标定")
        while True:
            response = uds.client.routine_control(0x03_A5, services.RoutineControl.ControlType.requestRoutineResults)
            if response.service_data.routine_status_record.hex() == "01":
                logger.info('Calibration running')
                time.sleep(2)
                continue
            elif response.service_data.routine_status_record.hex() == "02":
                logger.info("Calibration finished")
                break
            elif response.service_data.routine_status_record.hex() == "03":
                logger.error("Calibration failed")
                break
            elif response.service_data.routine_status_record.hex() == "04":
                logger.error("UNABLE_TO_LOCATE_TARGET图像识别错误")
                break
            elif response.service_data.routine_status_record.hex() == "05":
                logger.error("ROLL_ANGLE_OUT_OF_TOLERANCE")
                break
            elif response.service_data.routine_status_record.hex() == "06":
                logger.error("TARGETS_AT_INCORRECT_DISTANCE")
                break
            elif response.service_data.routine_status_record.hex() == "07":
                logger.error("PITCH_ANGLE_OUT_OF_TOLERANCE")
                break
            elif response.service_data.routine_status_record.hex() == "08":
                logger.error("YAW_ANGLE_OUT_OF_TOLERANCE")
                break
            elif response.service_data.routine_status_record.hex() == "09":
                logger.error("INTRINSIC_CALIB_IMPLAUSIBLE-标定超时")
                break
            elif response.service_data.routine_status_record.hex() == "0A":
                logger.error("RESULT_WRITE_TO_PDM_FAILED")
                break
            elif response.service_data.routine_status_record.hex() == "FF":
                logger.error("FAILED_FOR_OTHER_REASONS")
                break
        uds.client.ecu_reset(1)
        logger.info('ecu reset success')
        time.sleep(5)
        # uds.client.read_dtc_information(2,9)
        # logger.info('read dtc')
        uds.client.change_session(0x60)
        logger.info('enter 60 session')
        uds.client.unlock_security_access(0x71)
        assert data.get_payload().hex() != uds.client.read_data_by_identifier(0xFD55).get_payload().hex()
        #     logger.info('标定数据更新成功')
        # else:
        #     logger.info('标定数据更新失败')

        if res := uds.client.read_data_by_identifier(0xE000):
            print(res.get_payload().hex())
            logger.info(f'Forward_Timeout:{res.get_payload().hex()[36:38]}')
            logger.info(f'Forward_Block:{res.get_payload().hex()[39:41]}')
        if res := uds.client.read_data_by_identifier(0xFD01):
            print(res.get_payload().hex())
            logger.info(f'Cali_Step:{res.get_payload().hex()[4:6]}')
            logger.info(f'SocSysSt:{res.get_payload().hex()[6:8]}')
            logger.info(f'Self_Cali_cnt:{res.get_payload().hex()[9:11]}')
            logger.info(f'cali_err_point:{res.get_payload().hex()[12:14]}')


@pytest.mark.repeat(2)
def test_01():
    start_fill_back()
    time.sleep(25)
    eol()
    logger.info('标定成功')
    kill_fill_back()
    time.sleep(1)


if __name__ == '__main__':
    pytest.main(['-vs'])
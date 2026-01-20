# coding:utf-8
import time

import click
from loguru import logger

from test_ark.qh01.ssh import J3B, TDA4
from test_ark.qh01.stress import reset, stress_testing


def check_j3b_function_group_state(target_fun_state):
    flag = True
    try:
        with J3B() as ssh:
            _cmd_show_all_state = "logcat -d|grep trans|awk -F ' ' '{print $9}'"
            _cmd_show_last_state = "logcat -d|grep trans|awk -F ' ' 'END {print $9}'"
            J3B_cmd_pool = [_cmd_show_all_state, _cmd_show_last_state]
            #
            for i, cmd in enumerate(J3B_cmd_pool):
                _, output, _ = ssh.exec_command(cmd)
                # output = stdout.read().decode()
                time.sleep(1)
                logger.debug(f"[J3B]check_j3b_function_group_state: " + cmd + f" output: {output}")
                # checker
                if i == 1 and target_fun_state not in output.strip():
                    flag = False
                    logger.error(
                        f"[J3B]check_j3b_function_group_state, funtion state error, target state: {target_fun_state}, acctual state: {output}"
                    )
    except Exception as e:
        logger.error(f"[J3B]check_j3b_function_group_state, Exception {e}")
        flag = False
    finally:
        return flag


def check_tda4_function_group_state(ssh, target_fun_state, target_sys_state):
    flag = True
    try:
        _cmd_show_state = "source /opt/qh01/target/setenv.bash; /opt/qh01/target/application/bin/execution_tools group All "  # noqa: E501
        _cmd_filter_fun_state = "source /opt/qh01/target/setenv.bash; /opt/qh01/target/application/bin/execution_tools group All  |grep 'AutoDrive'|awk -F ' ' '{print $4}'"  # noqa: E501
        _cmd_filter_p_state = "source /opt/qh01/target/setenv.bash; /opt/qh01/target/application/bin/execution_tools group All  |grep Terminated|wc -l"  # noqa: E501
        _cmd_filter_sys_state = "source /opt/qh01/target/setenv.bash; /opt/qh01/target/application/bin/execution_tools group All  |grep 'SystemState'|awk -F ' ' '{print $4}'"  # noqa: E501
        tda4_cmd_pool = [_cmd_show_state, _cmd_filter_fun_state, _cmd_filter_p_state, _cmd_filter_sys_state]
        #
        for i, cmd in enumerate(tda4_cmd_pool):
            _, output, _ = ssh.exec_command(cmd)
            # output = stdout.read().decode()
            time.sleep(1)
            logger.debug(f"[TDA4]check_tda4_function_group_state, cmd: " + cmd + f" output: {output}")
            # checker
            output = output.strip()
            if i == 1:
                if target_fun_state not in str(output):
                    flag = False
                    logger.error(
                        f"[TDA4]check_tda4_function_group_state, funtion state error, target state: {target_fun_state}, acctual state: {output} len:{len(output)}"
                    )

            if i == 2:
                if int(output) != 0:
                    flag = False
                    logger.error(f"[TDA4]check_tda4_function_group_state, {output} processes were terminated")
            if i == 3:
                if target_sys_state not in str(output):
                    flag = False
                    logger.error(
                        f"[TDA4]check_tda4_function_group_state, system state error, target state: {target_sys_state}, acctual state: {output} len:{len(output)}"
                    )
    except Exception as e:
        logger.error(f"[TDA4]check_tda4_function_group_state, Exception {e}")
        flag = False
    finally:
        return flag


def function_group_switch_tda4(ssh, interval) -> tuple[int, int]:
    running_res = 0
    switch_pool = list()
    try:
        _, output, _ = ssh.exec_command("ls -l /userdata/log/core/")
        # output = stdout.read().decode()
        logger.debug(f"[TDA4]start ls -l/userdata/log/core/,  output: {output}")
        #
        _cmd_switch_to_parking = "source /opt/qh01/target/envsetup.sh;  /opt/qh01/target/bin/sm_client_tools -o set -f AutoDrive -s parking -t 20000"  # noqa: E501
        _cmd_switch_to_driving = "source /opt/qh01/target/envsetup.sh;  /opt/qh01/target/bin/sm_client_tools -o set -f AutoDrive -s driving -t 20000"  # noqa: E501
        #
        _cmd_switch_to_normal = "source /opt/qh01/target/envsetup.sh; /opt/qh01/target/bin/sm_client_tools -o set -f SystemState -s normal -t 20000"  # noqa: E501
        _cmd_switch_to_ota = "source /opt/qh01/target/envsetup.sh; /opt/qh01/target/bin/sm_client_tools -o set -f SystemState -s ota -t 20000"  # noqa: E501
        _cmd_switch_to_eol = "source /opt/qh01/target/envsetup.sh; /opt/qh01/target/bin/sm_client_tools -o set -f SystemState -s eol_calibration -t 20000"  # noqa: E501
        _cmd_switch_to_online = "source /opt/qh01/target/envsetup.sh; /opt/qh01/target/bin/sm_client_tools -o set -f SystemState -s onl_calibration  -t 20000"  # noqa: E501
        _cmd_switch_to_static = "source /opt/qh01/target/envsetup.sh; /opt/qh01/target/bin/sm_client_tools -o set -f SystemState -s static_calibration   -t 20000"  # noqa: E501
        #
        switch_pool = [
            {"cmd": _cmd_switch_to_driving, "args": ["driving", "normal"]},
            {"cmd": _cmd_switch_to_parking, "args": ["parking", "normal"]},
            {"cmd": _cmd_switch_to_eol, "args": ["calibration", "eol_calibration"]},
            {"cmd": _cmd_switch_to_normal, "args": ["parking", "normal"]},
            {"cmd": _cmd_switch_to_driving, "args": ["driving", "normal"]},
            {"cmd": _cmd_switch_to_online, "args": ["calibration", "onl_calibration"]},
            {"cmd": _cmd_switch_to_normal, "args": ["parking", "normal"]},
            {"cmd": _cmd_switch_to_driving, "args": ["driving", "normal"]},
            {"cmd": _cmd_switch_to_static, "args": ["calibration", "static_calibration"]},
            {"cmd": _cmd_switch_to_normal, "args": ["parking", "normal"]},
            {"cmd": _cmd_switch_to_driving, "args": ["driving", "normal"]},
            {"cmd": _cmd_switch_to_ota, "args": ["off", "ota"]},
        ]

        for i, cmd_dict in enumerate(switch_pool):
            _, output, _ = ssh.exec_command(cmd_dict["cmd"])
            # output = stdout.read().decode()
            logger.debug(f"[TDA4]function_group_switch_tda4: " + cmd_dict["cmd"] + f" output: {output}")
            time.sleep(interval)
            res = check_tda4_function_group_state(ssh, cmd_dict["args"][0], cmd_dict["args"][1])
            if res:
                running_res |= 1 << i
    except Exception as e:
        logger.error(f"[TDA4]function_group_switch_tda4 failed.")
        logger.exception(e)
    finally:
        return len(switch_pool), running_res


@logger.catch(reraise=False)
def main(current: int, reset_method: str, interval: int, *args, **kwargs):  # noqa
    tar_file = "/userdata/log.tar.gz"
    reset(method=reset_method)
    while not TDA4.is_online():
        time.sleep(3)
    time.sleep(20)
    with TDA4() as ssh:
        case_nums, res = function_group_switch_tda4(ssh, interval)
        for i in range(case_nums):
            logger.info(f"function_group_switch_tda4 result: {(res >> i) & 0x1} ")
        ssh.exec_command(f"sync; tar zcvf {tar_file} /userdata/log/")
        ssh.download_file(tar_file, local_dir=f"log/{current}.tar.gz")
        ssh.exec_command(f"rm -f {tar_file}")
        ssh.exec_command(f"rm -rf /userdata/log/core/;sync")


@click.command()
@click.option("--count", type=int, default=1, help="测试次数")
@click.option("--interval", type=int, default=30, help="每次功能组切换的时间间隔")
@click.option("--reset-method", type=click.Choice(["doip", "power", "relay"]), required=True, help="重启方式")
def cli(count: int, interval: int, reset_method: str):
    """压力测试-TDA4功能组切换"""
    stress_testing(main, count=count, interval=interval, reset_method=reset_method)


if __name__ == "__main__":
    cli()

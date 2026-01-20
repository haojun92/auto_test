import os
import time
import re
from venv import logger
from pythonping import ping
from loguru import logger
from ssh import SSH


class J3Mono(SSH):
    hostname: str = os.getenv("J3Mono", "172.16.100.2")
    port: int = 22
    username: str = "root"
    password: str = ""

    def __init__(self) -> None:
        super().__init__(self.hostname, self.port, self.username, self.password)

    @classmethod
    def is_online(cls) -> bool:
        return ping(cls.hostname).success()

    def now(self) -> str:
        _, now, _ = self.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        return now

    def test_dz_app_sts(self):
        chery_cmd = "ps w |grep chery"
        _, output, _ = self.exec_command(chery_cmd)
        mapfusion = '/mnt/chery/mapfusion/initrc.sh'
        sys_monitor = '/mnt/chery/system_monitor/initrc.sh'
        someip = '/mnt/chery/SomeipService/initrc.sh'
        resource_sts = '/mnt/chery/resource_statistics/initrc.sh'
        spi_route = '/mnt/chery/spi_route/initrc.sh'
        lst = output.lstrip().split('\n')
        map, monitor, sip, resource, spi = '','','','',''
        for line in lst:
            if (mapfusion in line or sys_monitor in line
                    or someip in line or resource_sts in line
                    or spi_route in line):
                process_num = line.strip().split(' ')[0]
                self.exec_command(f"kill -9 {process_num}")
                logger.info('kill success')
        _, output, _ = self.exec_command(chery_cmd)
        lst = output.lstrip().split('\n')

        for line in lst:
            if mapfusion in line:
                logger.debug('mapfusion process is running')
                map = True
            if sys_monitor in line:
                logger.debug('system_monitor is running ')
                monitor = True
            if someip in line:
                logger.debug('SomeipService is running ')
                sip = True
            if resource_sts in line:
                logger.debug('resource_statistics is running ')
                resource = True
            if spi_route in line:
                logger.debug('spi_route is running ')
                spi = True
        condition = [map, monitor, sip, resource, spi]
        if all(condition):
            logger.info('chery case pass')

    def test_apa_sts(self):
        apa_cmd = "ps w |grep apa"
        _, output, _ = self.exec_command(apa_cmd)
        app_rpc = '/mnt/apa/initrc.sh'
        xauto_b_ctrl = '/app/apa/bin/xauto-b-ctrl'
        apa_autoai = '/app/apa/bin/apa_autoai'

        app_rpc_sts, xauto_b_ctrl_sts, apa_autoai_sts = '', '', ''

        lst = output.lstrip().split('\n')

        for line in lst:
            if app_rpc in line:
                logger.debug('app_rpc process is running')
                app_rpc_sts = True
            if xauto_b_ctrl in line:
                logger.debug('xauto_b_ctrl is running ')
                xauto_b_ctrl_sts = True
            if apa_autoai in line:
                logger.debug('apa_autoai is running ')
                apa_autoai_sts = True

        condition = [app_rpc_sts, xauto_b_ctrl_sts, apa_autoai_sts]
        if all(condition):
            logger.info('apa case pass')

    def test_hobot_sts(self):
        cmd = "ps w |grep adas"
        _, output, _ = self.exec_command(cmd)
        adas = '/mnt/adas/initrc.sh'
        dump_ctrl = '/mnt/adas/adas-rt/bin/dump_ctrl.sh'
        adas_workflow = '/mnt/adas/adas-rt/hobot-adas-workflow /mnt/adas/adas-rt/config/global.json 1'

        lst = output.lstrip().split('\n')
        adas_workflow_sts, dump_ctrl_sts, adas_sts = '', '', ''

        for line in lst:
            if adas_workflow in line:
                logger.debug('adas_workflow process is running')
                adas_workflow_sts = True
            if dump_ctrl in line:
                logger.debug('dump_ctrl is running ')
                dump_ctrl_sts = True
            if adas in line:
                logger.debug('adas is running ')
                adas_sts = True

        condition = [adas_workflow_sts, dump_ctrl_sts, adas_sts]
        if all(condition):
            logger.info('adas case pass')

    def all_cpu_monitor(self):
        cmd = 'sar -u 1 5' # 采取10s数据，1s取一次值
        _, output, _ = self.exec_command(cmd)
        print(output)
        cpu = output.strip().split('\n')[-1].split(' ')[-1]
        if  float(cpu) < 90:
            logger.info(f'{cpu} less than 90,pass!')


    def parking_cpu_monitor(self):
        _cmd='''  ps | grep apa | grep -v grep | awk '{print $1, $7}' '''
        _, output, _ = self.exec_command(_cmd)
        pid_lst = []
        for i in  output.strip().split('\n'):
            if 'initrc.sh' not in i:
                pid_lst.append(i.split(' ')[0])
        count = 10 #统计的次数
        cmd = f"top -b -n {count} | grep -E '{pid_lst[0]}|{pid_lst[1]}|{pid_lst[2]}'"
        _, output1, _ = self.exec_command(cmd)
        print(output1)
        _sum = 0.0
        for line in output1.split('\n'):
            if 'apa' in line:
                _num = line.split(' ')[-2]
                _sum = float(_num)+_sum
        apa_sum = _sum/count
        if apa_sum < 5.0:
            logger.info(f'{apa_sum} less than 5%, pass')
        else:
            logger.error(f'{apa_sum} avg is large....,failed')

        pass

    def get_cpu_monitor(self,process_name,target):
        _cmd = '''ps -w | grep chery | grep -v grep | awk '{print $1, $9}' '''
        _, output, _ = self.exec_command(_cmd)
        pid_lst = []
        pid = 0
        for i in output.strip().split('\n'):
            if f'{process_name}' in i:
                pid = i.split(' ')[0]
                # pid_lst.append(i.split(' ')[0])
        print(pid)

        count = 10  # 统计的次数
        cmd = f"top -b -n {count} | grep {pid}"
        _, output1, _ = self.exec_command(cmd)
        _sum = 0.0
        for line in output1.split('\n'):
            if f'{process_name}' in line:
                _num = line.strip().split('{')[0].strip().split(' ')[-1]
                _sum = float(_num) + _sum
        avg_sum = _sum / count
        if avg_sum < target:
            logger.info(f'{avg_sum} less than {target}, pass')
        else:
            logger.error(f'{avg_sum} avg is large....,failed')
        # pass

    def dz_cpu_monitor(self):
        self.get_cpu_monitor('mapfusion',6)
        self.get_cpu_monitor('system_monitor',3)
        self.get_cpu_monitor('spi_route',4)

    def dz_log(self):
        _cmd = "cd /userdata/log/zdrive && du -sh *"
        _, output, _ = self.exec_command(_cmd)
        print(output.strip().split('\n'))
        for i in output.strip().split('\n'):
            print(i)
            if 'K' in i:
                num = float(re.findall(r"\d+\.?\d*",i)[0])/1024
            else:
                num = re.findall(r"\d+\.?\d*",i)[0]
            if float(num) < 50:
                logger.info('mem is less than 50')
            else:
                self.exec_command('export PATH=$PATH:/sbin; /sbin/reboot')
                time.sleep(5)
                self.__init__()
                time.sleep(5)
                _, output1, _ = self.exec_command(_cmd)
                for j in output1.strip().split('\n'):
                    if float(re.findall(r"\d+\.?\d*",j)[0]) < 51:
                        logger.info('mem is less than 50~~')
                    else:
                        logger.error('mem is more than 50')
        pass

    def get_mem(self,str1):
        num = 0
        if 'K' in str1:
            num = float(re.findall(r"\d+\.?\d*", str1)[0]) / 1024
        else:
            num = re.findall(r"\d+\.?\d*", str1)[0]
        return num

    def ls_log(self):
        _cmd = "cd /userdata/log/ && du -sh *"
        _, output, _ = self.exec_command(_cmd)
        print(output.strip().split('\n'))
        for i in output.strip().split('\n'):
            if 'lisheng' in i:
                ls_num = self.get_mem(i)
                if float(ls_num) < 350:
                    logger.info(f"{ls_num} is less than 350,pass")
                else:
                    logger.error(f"{ls_num} is more than 350,fail")

            elif 'navinfo' in i:
                navinfo_num = self.get_mem(i)
                if float(navinfo_num) < 200:
                    logger.info(f"{navinfo_num} is less than 200,pass")
                else:
                    logger.error(f"{navinfo_num} is more than 200,fail")

    def topic_check(self):
        # 订阅者
        import zmq

        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://192.0.0.1:5555")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # while True:
        #     news = socket.recv_string()
        #     print("Received News: {}".format(news))
        pass


if __name__ == '__main__':
    J3 = J3Mono()
    # J3.test_dz_app_sts()
    # J3.test_apa_sts()
    # J3.test_hobot_sts()
    # J3.parking_cpu_monitor()
    # J3.dz_cpu_monitor()
    # J3.dz_log()
    # J3.ls_log()
    J3.topic_check()

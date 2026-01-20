import os
import threading
import time
from asyncio import timeout
from configparser import Error
from datetime import datetime
from itertools import count, repeat
from pathlib import Path
from scapy.all import *
import pytest
import paramiko
import paramiko.auth_strategy
from scp import SCPClient
import click
import udsoncan
from loguru import logger
from udsoncan import services, MemoryLocation
from udsoncan.services import DiagnosticSessionControl

# from test_ark.t1gc.doip import DoIP
from doip import DoIP
from udsoncan.services import ECUReset

def get_log():


    class AuthStrategy(paramiko.auth_strategy.AuthStrategy):

        def __init__(self, ssh_config, username):
            super().__init__(ssh_config)
            self.username = username

        def get_sources(self):
            yield paramiko.auth_strategy.NoneAuth(self.username)

    hostname = '192.168.2.11'
    username = 'root'

    ssh_config = paramiko.SSHConfig()
    auth_strategy = AuthStrategy(ssh_config, username)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client = ssh.connect(hostname, auth_strategy=auth_strategy)
    # stdin, stdout, stderr = ssh.exec_command('scp -r /userdata/log/lisheng/fota')
    # print(stdout.read().decode("utf-8"))
    # subprocess.Popen(['scp -r','root@192.168.2.11:/userdata/log/lisheng/*','./'])



    ssh_config = paramiko.SSHConfig()
    auth_strategy = AuthStrategy(ssh_config, username)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, auth_strategy=auth_strategy)

    with SCPClient(ssh.get_transport()) as scp:
        local_path = os.getcwd()+'\\'+f'{time.strftime('%Y-%m-%d-%H-%M-%S')}'
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        scp.get('/userdata/log/lisheng/fota_log/', local_path, recursive=True)
    stdin, stdout, stderr = ssh.exec_command('rm -rf /userdata/log/lisheng/fota')




def get_zip_length(file_path):
    import os,binascii,codecs
    zip_length = os.path.getsize(file_path)
    length = hex(zip_length)[2:].upper()
    print(f"The length of the ZIP package is {length}.")
    parts = [length[i:i + 2] for i in range(0, len(length), 2)]
    return length,parts



def read_rsa(file_path):
    with open(file_path,'r') as f:
        temp = f.readlines()[0].replace('0x','').replace(',','')
    return bytes.fromhex(temp)


def main(rsa_file: str ='D:/ota/1030/IDCU_2_2_ASW1_Full_UDS_20241107.rsa',zip_file :str = 'D:/ota/1030/1030.zip'):
    try:
        with DoIP() as doip:
            res = doip.client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession) # 10 03
            if '5003' in res.get_payload().hex():
                logger.info('enter extend session')
            else:
                logger.info('enter extend session failed')
                raise Error
            response = doip.client.routine_control(
                0xD0_03, services.RoutineControl.ControlType.startRoutine
            )  # 31 01 D0 03
            logger.info('Condition check')
            if response.get_payload().hex() == '7101d00301':
                logger.info("Condition not satisfied")
                raise RuntimeError("Condition not satisfied")
            doip.client.control_dtc_setting(services.ControlDTCSetting.SettingType.off) # 85 03
            logger.info('dtc setting off')
            doip.client.communication_control(0x01, 0x03) # 28 01 03
            logger.info('communication off')
            doip.client.change_session(DiagnosticSessionControl.Session.programmingSession) # 10 02
            logger.info('enter 02 session')
            doip.client.unlock_security_access(0x07) # 27 07
            logger.info('security access')
            doip.client.write_data_by_identifier(0xF15A,'012345678901234')
            logger.info('read f15a')
            doip.client.routine_control(0xD0_04,services.RoutineControl.ControlType.startRoutine,data=read_rsa(rsa_file)) # 31 01 D0 04
            logger.info('dependencies check')
            length,parts = get_zip_length(zip_file)
            # doip.client.routine_control(
            #     0xFF_00,
            #     services.RoutineControl.ControlType.startRoutine,
            #     data=bytes([0x44, 0x00, 0x00, 0x00,0x00,int(parts[0], 16),int(parts[1], 16),int(parts[2], 16),int(parts[3], 16)]),
            # )  # 31 01 FF 00
            # logger.info('erase mem')
            # doip.client.routine_control(
            #     0xFF_00,
            #     services.RoutineControl.ControlType.startRoutine,
            #     # data=bytes([0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1C, 0xE6]),
            #     data=bytes([0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x12, 0xEF, 0x88]),
            # )  # 31 01 FF 00
            #
            memory_location = MemoryLocation(address=int(bytes([0x00, 0x00, 0x00, 0x00]).hex(), 16),
                                             memorysize=int(length,16),
                                             address_format=32, memorysize_format=32)
            doip.client.request_download(memory_location=memory_location)  # 34 00 44 00
            retrans_count=0
            while retrans_count < 3:
                start_time = time.time()
                res = doip.transfer_data_service(zip_file) # 36 01
                while True:
                    if res:
                        break

            logger.info('start transfer data')
            doip.client.request_transfer_exit()  # 37
            logger.info('exit transfer')
            res = doip.client.routine_control(0xD0_02, services.RoutineControl.ControlType.startRoutine, data=read_rsa(rsa_file)) # 31 01 D0 02
            if res.get_payload().hex() == '7101d00201':
                logger.info("incorrectResult")
                raise RuntimeError("incorrectResult")

            res = doip.client.routine_control(0xff_01, services.RoutineControl.ControlType.startRoutine,
                                              )  # 31 01 ff 01
            if res.get_payload().hex() == '7101ff0101':
                logger.info("incorrectResult")
            doip.client.routine_control(0xd0_05, services.RoutineControl.ControlType.startRoutine)  # 31 01 d0 05
            while True:
                res = doip.client.routine_control(0xd0_05, services.RoutineControl.ControlType.requestRoutineResults) # 31 03 d0 05
                if '7103d00502' in res.get_payload().hex():
                    logger.info('install completed')
                    assert True
                    break
                elif '7103d00503' in res.get_payload().hex():
                    continue
                elif '7103d00505' in res.get_payload().hex():
                    logger.error('install failure')
                    raise RuntimeError("install failure")
                    # break
                # else:
                #     logger.error('install error')
                time.sleep(1)
            doip.hard_reset() # 11 01
            logger.error('ecu reset')
            time.sleep(20)
        with DoIP() as doip:
            doip.client.change_session(DiagnosticSessionControl.Session.defaultSession) # 10 01
            logger.info('enter 10 01')
            res =doip.client.clear_dtc() # 14
            logger.info('clear dtc')
            try:
                assert res.get_payload().hex() == '54'
                logger.info('ota success!!!')
            except Exception:
                logger.info('ota failed')
                raise Error
    except Exception:
        get_log()
        raise Error

class PacketSniffer:
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.sniffer_thread = None
        self.is_sniffing = False
        self.running = Event()

    def start_sniffing(self):
        self.is_sniffing = True
        self.running.set()
        self.sniffer_thread = threading.Thread(target=self.sniff)
        self.sniffer_thread.start()

    def stop_sniffing(self):
        self.running.clear()
        self.is_sniffing = False
        self.sniffer_thread.join()

    def sniff(self):
        # Start sniffing packets and save to pcap file
        print(f"Sniffing packets and saving to {self.pcap_file}...")
        # sniff(prn=self.process_packet, store=0, filter="uds", stop_filter=lambda x: not self.is_sniffing)
        sniff(prn=self.process_packet, store=0,iface="以太网 7", filter='udp port 13400',timeout=540)
        print("Stopped sniffing.")

    def process_packet(self, packet):
        # Save packet to pcap file
        wrpcap(self.pcap_file, packet, append=True)



class TestOTA:
    @pytest.mark.repeat(1)
    # @click.command()
    # @click.option("--count", type=int, default=100, help="升级次数")
    def test_01(self) -> None:
        # pcap_file = "ota.pcap"
        # sniffer = PacketSniffer(pcap_file)
        # sniffer.start_sniffing()
        """ota test"""
        # for i in range(1, num + 1):
        #     logger.info("*" * 80)
        #     logger.info(f"开始第 {i} 次升级")
        #     logger.info("*" * 80)
        #     main(num=i)
        main()
        # path = "D:/code/test_ark/test_ark/t1gc/T1GC_IDCU_FOTA_20240919/IDCU_FOTA2.exe"
        # result = subprocess.run([path], check=True, capture_output=True, text=True, input="\n")
        # print(result.stdout)
        # if 'failed during the ' in result.stdout:
        #     print('ota error')
        # elif '[FOTA] successfully completed' in result.stdout:
        #     print('ota success')
        # sniffer.stop_sniffing()



if __name__ == "__main__":
    pytest.main([])




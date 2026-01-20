import os
import time
from asyncio import timeout
from datetime import datetime
from logging.config import stopListening

import paramiko
import paramiko.auth_strategy

class AuthStrategy(paramiko.auth_strategy.AuthStrategy):

    def __init__(self, ssh_config, username):
        super().__init__(ssh_config)
        self.username = username

    def get_sources(self):
        yield paramiko.auth_strategy.NoneAuth(self.username)
#
# hostname = '192.168.2.11'
# username = 'root'
#
# ssh_config = paramiko.SSHConfig()
# auth_strategy = AuthStrategy(ssh_config, username)
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client = ssh.connect(hostname, auth_strategy=auth_strategy)
# # stdin, stdout, stderr = ssh.exec_command('scp -r /userdata/log/lisheng/fota')
# # print(stdout.read().decode("utf-8"))
# # subprocess.Popen(['scp -r','root@192.168.2.11:/userdata/log/lisheng/*','./'])
#
# from scp import SCPClient
#
# ssh_config = paramiko.SSHConfig()
# auth_strategy = AuthStrategy(ssh_config, username)
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect(hostname, auth_strategy=auth_strategy)

# with SCPClient(ssh.get_transport()) as scp:
#     scp.get('/userdata/log/lisheng/fota_log/', 'D:/code/test_ark/test_ark/t1gc', recursive=True)
# print(time.time())
# local_path = os.getcwd()+'\\'+f'{time.strftime('%Y-%m-%d-%H-%M-%S')}'
# if not os.path.exists(local_path):
#     os.makedirs(local_path)
import pyshark
from scapy.all import *
# dpkt  = sniff(iface = "以太网 7",filter='udp port 13400')
# # capture = pyshark.LiveCapture(interface='以太网 7',output_file="ota.pcap")
# #
# # for packet in capture.sniff_continuously():
# #     if 'uds' in packet:
# #         print(packet)
# wrpcap("demo.pcap", dpkt)
#
# from scapy.all import *

# def packet_callback(packet):

class PacketSniffer:
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.sniffer_thread = None
        self.is_sniffing = False

    def start_sniffing(self):
        self.is_sniffing = True
        self.sniffer_thread = threading.Thread(target=self.sniff)
        self.sniffer_thread.start()

    def stop_sniffing(self):
        self.is_sniffing = False
        self.sniffer_thread.join()

    def sniff(self):
        # Start sniffing packets and save to pcap file
        print(f"Sniffing packets and saving to {self.pcap_file}...")
        # sniff(prn=self.process_packet, store=0, filter="uds", stop_filter=lambda x: not self.is_sniffing)
        sniff(prn=self.process_packet, store=0,iface="以太网 7", filter='ip',timeout=10)
        print("Stopped sniffing.")

    def process_packet(self, packet):
        # Save packet to pcap file
        wrpcap(self.pcap_file, packet, append=True)

# if __name__ == '__main__':
    # pcap_file = "packets.pcap"
    # sniffer = PacketSniffer(pcap_file)
    # sniffer.start_sniffing()
    #
    # sniffer.stop_sniffing()
        import os
        #
main = "D:/code/test_ark/test_ark/t1gc/T1GC_IDCU_FOTA_20240919/IDCU_FOTA.exe"
# r_v = os.system(main)
# print(r_v)
import subprocess
import threading
import os
import pytest


# @

print(len('''050000 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0000 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0000 00 00 00 00 00 00 00 00 00 00 00 00 00 00 D0 01'''.replace(' ','')))


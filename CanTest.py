import sys
from DBCAnalyzer import DBCAnalyzer
from zlgcan import Zlgcan, ZCAN
import argparse
import numpy
import time
import datetime
# import GenerateExcel
import multiprocessing
import threading

CAN_TEST_MODE = {"TR_TEST":0, "MAX_VLUAE_TEST":1, "MIN_VALUE_TEST":2}

class CANTx_Test:
    def __init__(self, dbc_msg):
        self.dbc_msg = dbc_msg
        self.tx_or_rx_cnt = 0
        self.last_tx_or_rx_time = 0
        self.tr_test_result = 'gray' #green:测试通过 red：测试失败  gray：未测试
        self.period_test_result = 'gray' 
        self.max_value_test_result = 'gray'
        self.mid_value_test_result = 'gray'
        self.min_value_test_result = 'gray'
        self.period_test_err_cnt = 0
        self.actual_period = 0
        self.signal_data_max = {}
        self.signal_data_mid = {}
        self.signal_data_min = {}
        self.signal_data = {}
        self.physics_data = ""
        self.check_data = ""
        self.store_max_check_data = ""
        self.store_mid_check_data = ""
        self.store_min_check_data = ""
        self.test_mode = ""

        self.valid_result = {True:'green', False:'red'}
        self.store_data_dict = {'Max有效值测试':self.store_max_check_data,
                                'Mid有效值测试':self.store_mid_check_data,
                                'Min有效值测试':self.store_min_check_data}
        self.all_data_check_dict = {'Max有效值测试':self.max_value_test_result,
                                    'Mid有效值测试':self.mid_value_test_result,
                                    'Min有效值测试':self.min_value_test_result} 

        multiplexer_signal= []
        for signal in self.dbc_msg.signals:
            if signal.is_multiplexer is False:
                min_value, max_value, mid_value = self.calculate_signal_values(signal)
                self.signal_data_max[signal.name] = max_value
                self.signal_data_min[signal.name] = min_value
                self.signal_data_mid[signal.name] = mid_value 
            else:
                initial = False
                for key, value in self.dbc_msg._codecs['multiplexers'][signal.name].items():
                   if initial == False:
                        initial = True
                        self.signal_data_max[signal.name]  = key
                        self.signal_data_min[signal.name]  = key
                        self.signal_data_mid[signal.name]  = key
                        for key, sub_signal_list in value.items():
                            if key == 'signals':
                                for sub_signal in sub_signal_list:
                                    min_value, max_value, mid_value = self.calculate_signal_values(sub_signal)
                                    self.signal_data_max[sub_signal.name] = max_value
                                    self.signal_data_min[sub_signal.name] = min_value
                                    self.signal_data_mid[sub_signal.name] = mid_value 
                   else:
                       for key, sub_signal_list in value.items():
                            if key == 'signals':
                                for sub_signal in sub_signal_list:
                                    multiplexer_signal.append(sub_signal.name)

        for remove_signal_name in multiplexer_signal:
            self.signal_data_max.pop(remove_signal_name, None)
            self.signal_data_min.pop(remove_signal_name, None)
            self.signal_data_mid.pop(remove_signal_name, None) 

        #defaule test mode
        self.setTestMode('收发测试')

    def clear(self):
        self.tx_or_rx_cnt = 0
        self.last_tx_or_rx_time = 0
        self.tr_test_result = 'gray' #green:测试通过 red：测试失败  gray：未测试
        self.period_test_result = 'gray' 
        self.max_value_test_result = 'gray'
        self.mid_value_test_result = 'gray'
        self.min_value_test_result = 'gray'
        self.period_test_err_cnt = 0
        self.actual_period = 0
        self.physics_data = ""
        self.check_data = ""
        self.store_max_check_data = ""
        self.store_mid_check_data = ""
        self.store_min_check_data = ""
        self.setTestMode(self.test_mode)

    def setTestMode(self, test_mode):
        if test_mode == '收发测试':
            self.physics_data  = self.dbc_msg.encode(self.signal_data_min)
            self.signal_data  = self.signal_data_min
        elif test_mode == 'Max有效值测试':
            self.physics_data  = self.dbc_msg.encode(self.signal_data_max)
            self.signal_data  = self.signal_data_max
        elif test_mode == 'Mid有效值测试':
            self.physics_data  = self.dbc_msg.encode(self.signal_data_mid)
            self.signal_data  = self.signal_data_mid
        elif test_mode == 'Min有效值测试':
            self.physics_data  = self.dbc_msg.encode(self.signal_data_min)
            self.signal_data  = self.signal_data_min

        self.test_mode = test_mode
      
    def calculate_signal_values(self, signal):
        # 提取信号的属性
        bit_length = signal.length
        offset = signal.offset
        factor = signal.scale
        is_signed = signal.is_signed
        data_type = signal.choices  # 假设 signal.choice 提供了数据类型的信息

        # 计算最大值和最小值
        if is_signed:
            max_raw_value = (1 << (bit_length - 1)) - 1
            min_raw_value = - (1 << (bit_length - 1))
        else:
            max_raw_value = (1 << bit_length) - 1
            min_raw_value = 0   

        # 使用信号的预设最大值和最小值（如果存在）
        max_value = signal.maximum if signal.maximum is not None else max_raw_value * factor + offset
        min_value = signal.minimum if signal.minimum is not None else min_raw_value * factor + offset

        mid_value = (max_value+min_value)/2

        # 根据数据类型调整值
        if data_type == 'int':
            max_value = int(max_value)
            min_value = int(min_value)
            mid_value = int(mid_value)
        elif data_type == 'float':
            max_value = numpy.finfo(numpy.float32).max
            min_value = numpy.finfo(numpy.float32).min
            mid_value = max_value / 2
        elif data_type == 'double':
            max_value = numpy.finfo(numpy.float64).max
            min_value = numpy.finfo(numpy.float64).min
            mid_value = max_value / 2

        return min_value, max_value, mid_value
 
    def period_check(self, period_100us): # period_100us: 100us/1
        delt_time = abs(period_100us - self.dbc_msg.cycle_time*10)
        if delt_time > self.dbc_msg.cycle_time:
            self.period_test_err_cnt+=1
            if self.period_test_err_cnt > 100:
                self.period_test_result = 'red' 
        elif self.period_test_result  != 'red':
             self.period_test_err_cnt-=1
             self.period_test_result = 'green' 
        self.actual_period  = period_100us/10

    def tr_check(self, tr_result):
        if  tr_result == True:
            self.tr_test_result = 'green'
        else:
            self.tr_test_result = 'red'

    def Value_check(self, check_physic_value):
        self.check_data = check_physic_value
        if self.physics_data != "":
            check_result = (check_physic_value == self.physics_data)
            self.all_data_check_dict  = self.valid_result[check_result]
            self.store_data_dict[self.test_mode] = check_physic_value          

def period_check(dbc_analyzer_obj, zcanlib, chn0_handle):
    PERIOD_EST_NUM = 50
    period_test_cnt = 0
    period_pass_cnt = 0
    period_fail_cnt = 0
    for channel_obj in dbc_analyzer_obj.channel_obj_list:
        print("Channel_Name:",channel_obj.channel_name)
        for tx_msg in channel_obj.tx_msg_list:
            if tx_msg.send_type == 'Cyclic':
                rcv_msgs_list = []
                tx_msg_period_list = []# ms
                message_num = 0
                period_time_last = 0
                period_tolerance = 0
                period_sum = 0
                period_avg = 0
                period_err_cnt = 0
                period_avg_err = 0

                period_test_cnt += 1
                print("Message Name:",tx_msg.name,"\nMessage Id:",tx_msg.frame_id,"\nCycle Time:",tx_msg.cycle_time)
                msg_cycle_time = tx_msg.cycle_time
                if msg_cycle_time > 500:
                    period_tolerance = 50
                elif msg_cycle_time > 100:
                    period_tolerance = msg_cycle_time/10
                elif msg_cycle_time >= 20:
                    period_tolerance = 10
                else:
                    period_tolerance =5

                while message_num < PERIOD_EST_NUM+1:
                    rcv_canfd_msgs = Zlgcan.Message_Receive(zcanlib, chn0_handle)
                    for rcv_canfd_msg in rcv_canfd_msgs:
                        if tx_msg.frame_id == rcv_canfd_msg.frame.can_id:
                            rcv_msgs_list.append(rcv_canfd_msg)
                            message_num+=1
                for rcv_msg in rcv_msgs_list:
                    if period_time_last == 0:
                        period_time_last = rcv_msg.timestamp/1000
                    else:
                        tx_msg_period_list.append(round(rcv_msg.timestamp/1000-period_time_last,2))
                        period_time_last = rcv_msg.timestamp/1000

                for period in tx_msg_period_list:
                    period_sum += period
                    if abs(period-msg_cycle_time) > period_tolerance:
                        period_err_cnt+=1
                        print("Period Err Value:",period)
                period_avg = round(period_sum/PERIOD_EST_NUM,2)
                if abs(period_avg-msg_cycle_time) > msg_cycle_time/50:
                    period_avg_err = 1
                print("Period Num:",len(tx_msg_period_list))
                print("Period Max:",max(tx_msg_period_list))
                print("Period Min:",min(tx_msg_period_list))
                print("Period Avg:",period_avg)
                if period_avg_err > 0:
                    print("Average Period Out Of Range:")
                if period_err_cnt > 0:
                    print("Period Err Cnt:",period_err_cnt)
                if period_avg_err == 0 and period_err_cnt == 0:
                    period_pass_cnt += 1
                else:
                    period_fail_cnt += 1
    print("Number Of Test:",period_test_cnt)
    print("Pass:",period_pass_cnt)
    print("Fail:",period_fail_cnt)
################################################################################
#定义测试通道，测试通道会绑定相应的DBC通道
###############################################################################
class TestChannel:
    def __init__(self, dbc_channel):
        self.channel_name = dbc_channel.channel_name
        self.can_type = dbc_channel.can_type
        self.arbi_baudr = dbc_channel.arbi_baudr
        self.data_baudr = dbc_channel.data_baudr
        self.test_tx_msg = {}
        for tx_msg in dbc_channel.tx_msg:
            a_test_msg = TestMsg(tx_msg)
            self.test_tx_msg[tx_msg.frame_id] = a_test_msg
        
        self.test_rx_msg = {}
        for rx_msg in dbc_channel.rx_msg:
            a_test_msg = TestMsg(rx_msg)
            self.test_rx_msg[rx_msg.frame_id] = a_test_msg

    def setTestMode(self, test_mode):
        for msg_id, msg in self.test_tx_msg.items():
            msg.setTestMode(test_mode)
        for msg_id, msg in self.test_rx_msg.items():
            msg.setTestMode(test_mode)

    def clear(self):
        for msg_id, msg in self.test_tx_msg.items():
            msg.clear()
        for msg_id, msg in self.test_rx_msg.items():
            msg.clear()
        
class CanTest:
    def __init__ (self, dbc_channel_list):
        self.manager = multiprocessing.Manager()
        self.test_channel_list = self.manager.list()
        for dbc_channel in dbc_channel_list:
            a_test_channel = TestChannel(dbc_channel)
            self.test_channel_list.append(a_test_channel)

def InputParamLoad(): 
    Parse = argparse.ArgumentParser()
    Parse.add_argument('-p', 
                        '--path',
                        nargs=1, 
                        type=str,
                        default=None, 
                        help="input project path")
    Parse.add_argument('-c', 
                        '--cfg', 
                        nargs=1,
                        type=str, 
                        default=None, 
                        help="input cfg path") 
    InputArgs = Parse.parse_args()
    if InputArgs.path == None:
        print('Please input project work path!')
        Parse.print_help() 
        exit(-1)
    if InputArgs.cfg == None:
        print('Please input project config file!')
        Parse.print_help()
        exit(-1)
    return InputArgs 

def wait(sec):
    while sec > 0:
        print(f"测试中 ... {sec} seconds", end="\r")
        time.sleep(1)
        sec -= 1

def main():
    a_args = InputParamLoad()
    project_path =  a_args.path[0] 
    cfg_file_path = a_args.cfg[0]

    print("Step 1 DBC Analysis...")
    a_dbc_analyzer_obj = DBCAnalyzer(project_path, cfg_file_path)
    
    print("Step 2 Open Device...")
    zcanlib = ZCAN()
    handle = Zlgcan.Open_Device(zcanlib)

    print("Step 3 Open Channel...")
    chn0_handle = Zlgcan.canfd_start(zcanlib, handle, 0)
    print("channel0 handle:%d" %(chn0_handle))
    chn1_handle = Zlgcan.canfd_start(zcanlib, handle, 1)
    print("channel1 handle:%d" %(chn0_handle))

    print("Step 4 Run testcase...")
    print("CANTx Period Test Start...")
    period_check(a_dbc_analyzer_obj, zcanlib, chn0_handle)
    print("CANTx Period Test Done")

    print("Step 5 Close Channel...")
    ret=zcanlib.ResetCAN(chn0_handle)
    if ret==1:
        print("Close Channel0 success! ")
    ret=zcanlib.ResetCAN(chn1_handle)
    if ret==1:
        print("Close Channel1 success! ")

    print("Step 6 Close Device...")
    ret=zcanlib.CloseDevice(handle)
    if ret==1:
        print("Close Device success! ")

    #debug
    # output_path = "output.txt"
    # output_handler = open(output_path, "w", encoding='UTF-8')
    # channel_obj = a_dbc_analyzer_obj.channel_obj_list[0]
    # print('node:',channel_obj.node,file=output_handler)
    # print('channel_name:',channel_obj.channel_name,file=output_handler)
    # print('can_type:',channel_obj.can_type,file=output_handler)
    # print('arbi_baudr:',channel_obj.arbi_baudr,file=output_handler)
    # print('data_baudr:',channel_obj.data_baudr,file=output_handler)
    # print('dbc_file_list:',file=output_handler)
    # print(channel_obj.dbc_file_list,file=output_handler)
    # print('tx_msg:',file=output_handler)
    # for tx_msg in channel_obj.tx_msg_list:
    #     print(tx_msg.name,tx_msg.frame_id,tx_msg.length,tx_msg.senders,tx_msg.send_type,tx_msg.cycle_time,tx_msg.is_extended_frame,tx_msg.is_fd,file=output_handler)
    # print('rx_msg:',file=output_handler)
    # for rx_msg in channel_obj.rx_msg_list:
    #     print(rx_msg.name,rx_msg.frame_id,rx_msg.length,rx_msg.senders,rx_msg.send_type,rx_msg.cycle_time,rx_msg.is_extended_frame,rx_msg.is_fd,file=output_handler)
    # output_handler.close()

if __name__ == "__main__":
    main()
import lib.t32_launch as t32_launch
from lib.zuds import *
from lib.dh1766 import *
from lib.doip import DoIP
from ctypes import *
import itertools
import time
import subprocess

TEST_NUM = 100
UNUSEd_BIT_PATTERN = 0

CRC8_J1850_TABLE = [
0x00, 0x1D, 0x3A, 0x27, 0x74, 0x69, 0x4E, 0x53,
0xE8, 0xF5, 0xD2, 0xCF, 0x9C, 0x81, 0xA6, 0xBB,
0xCD, 0xD0, 0xF7, 0xEA, 0xB9, 0xA4, 0x83, 0x9E,
0x25, 0x38, 0x1F, 0x02, 0x51, 0x4C, 0x6B, 0x76,
0x87, 0x9A, 0xBD, 0xA0, 0xF3, 0xEE, 0xC9, 0xD4,
0x6F, 0x72, 0x55, 0x48, 0x1B, 0x06, 0x21, 0x3C,
0x4A, 0x57, 0x70, 0x6D, 0x3E, 0x23, 0x04, 0x19,
0xA2, 0xBF, 0x98, 0x85, 0xD6, 0xCB, 0xEC, 0xF1,
0x13, 0x0E, 0x29, 0x34, 0x67, 0x7A, 0x5D, 0x40,
0xFB, 0xE6, 0xC1, 0xDC, 0x8F, 0x92, 0xB5, 0xA8,
0xDE, 0xC3, 0xE4, 0xF9, 0xAA, 0xB7, 0x90, 0x8D,
0x36, 0x2B, 0x0C, 0x11, 0x42, 0x5F, 0x78, 0x65,
0x94, 0x89, 0xAE, 0xB3, 0xE0, 0xFD, 0xDA, 0xC7,
0x7C, 0x61, 0x46, 0x5B, 0x08, 0x15, 0x32, 0x2F,
0x59, 0x44, 0x63, 0x7E, 0x2D, 0x30, 0x17, 0x0A,
0xB1, 0xAC, 0x8B, 0x96, 0xC5, 0xD8, 0xFF, 0xE2,
0x26, 0x3B, 0x1C, 0x01, 0x52, 0x4F, 0x68, 0x75,
0xCE, 0xD3, 0xF4, 0xE9, 0xBA, 0xA7, 0x80, 0x9D,
0xEB, 0xF6, 0xD1, 0xCC, 0x9F, 0x82, 0xA5, 0xB8,
0x03, 0x1E, 0x39, 0x24, 0x77, 0x6A, 0x4D, 0x50,
0xA1, 0xBC, 0x9B, 0x86, 0xD5, 0xC8, 0xEF, 0xF2,
0x49, 0x54, 0x73, 0x6E, 0x3D, 0x20, 0x07, 0x1A,
0x6C, 0x71, 0x56, 0x4B, 0x18, 0x05, 0x22, 0x3F,
0x84, 0x99, 0xBE, 0xA3, 0xF0, 0xED, 0xCA, 0xD7,
0x35, 0x28, 0x0F, 0x12, 0x41, 0x5C, 0x7B, 0x66,
0xDD, 0xC0, 0xE7, 0xFA, 0xA9, 0xB4, 0x93, 0x8E,
0xF8, 0xE5, 0xC2, 0xDF, 0x8C, 0x91, 0xB6, 0xAB,
0x10, 0x0D, 0x2A, 0x37, 0x64, 0x79, 0x5E, 0x43,
0xB2, 0xAF, 0x88, 0x95, 0xC6, 0xDB, 0xFC, 0xE1,
0x5A, 0x47, 0x60, 0x7D, 0x2E, 0x33, 0x14, 0x09,
0x7F, 0x62, 0x45, 0x58, 0x0B, 0x16, 0x31, 0x2C,
0x97, 0x8A, 0xAD, 0xB0, 0xE3, 0xFE, 0xD9, 0xC4]

def crclib_getCRC8(Data_list, Data_Len, XOR_Value):
    crc = XOR_Value
    #calculate CRC8 conform to SAE J1850
    for idx in range(Data_Len): 
        crc = CRC8_J1850_TABLE[crc ^ (Data_list[idx])]
    #XOR
    crc ^= XOR_Value
    return crc

def res_check(zcanlib, chn_handle, req_data, res_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i] for i in range(response.response.positive.param_len)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    elif res_list != res_data[1:]:
        test_flg = 0
        print("Response error")

    return test_flg

def read_version(zcanlib, chn_handle, req_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i+2] for i in range(response.response.positive.param_len-2)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    else:
        print("Version is:",''.join(chr(i) for i in res_list))

    return test_flg

def get_response(zcanlib, chn_handle, req_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i] for i in range(response.response.positive.param_len)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    
    return res_list,test_flg

def unlock(seed):
    exe_path = "./lib/encryption.exe"
    level = "03"
    process = subprocess.Popen([exe_path, seed, level], stdout=subprocess.PIPE)
    output, error = process.communicate()  # 获取输出和错误信息
    
    return output.decode().strip()
    
def msg_check(dbc_analyzer_obj, zcanlib, chn_handle):
    tx_exp = set()
    for channel_obj in dbc_analyzer_obj.channel_obj_list:
        for tx_msg in channel_obj.tx_msg_list:
            if tx_msg.send_type == 'Cyclic':
                if tx_msg.frame_id not in tx_exp:
                    tx_exp.add(tx_msg.frame_id)
    tx_act = set()
    time_cnt = 30
    rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
    time.sleep(0.1)
    while time_cnt > 0:
        rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
        for rcv_can_msg in rcv_can_msgs:
            if rcv_can_msg.frame.can_id not in tx_act:
                tx_act.add(rcv_can_msg.frame.can_id)
        for rcv_canfd_msg in rcv_canfd_msgs:
            if rcv_canfd_msg.frame.can_id not in tx_act:
                tx_act.add(rcv_canfd_msg.frame.can_id)
        time_cnt -= 1
        time.sleep(0.1)
    # print(tx_exp)
    # print(tx_act)
    test_flg = 1
    if tx_act != tx_exp:
        test_flg = 0
    
    return test_flg

def get_msgs(all_can_list, all_canfd_list, tx_msg, test_num):
    rcv_can_list = []
    rcv_canfd_list = []
    message_num = 0
    for rcv_can_msg in all_can_list:
        if tx_msg.frame_id == rcv_can_msg.frame.can_id:
            rcv_can_list.append(rcv_can_msg)
            message_num+=1
            if message_num >= test_num:
                break

    for rcv_canfd_msgs in all_canfd_list:
        if tx_msg.frame_id == rcv_canfd_msgs.frame.can_id:
            rcv_canfd_list.append(rcv_canfd_msgs)
            message_num+=1
            if message_num >= test_num:
                break

    return rcv_can_list, rcv_canfd_list

def get_all_msgs(dbc_analyzer_obj, zcanlib, chn_handle, test_num):
    rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
    print("\nRecord Messages Start")
    rcv_can_list = []
    rcv_canfd_list = []
    for channel_obj in dbc_analyzer_obj.channel_obj_list:
        print("Channel_Name:",channel_obj.channel_name)
        for tx_msg in channel_obj.tx_msg_list:
            if tx_msg.send_type == 'Cyclic':
                message_num = 0
                time_wait = 20 #2s
                while message_num < test_num:
                    rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
                    for rcv_can_msg in rcv_can_msgs:
                        if tx_msg.frame_id == rcv_can_msg.frame.can_id:
                            rcv_can_list.append(rcv_can_msg)
                            message_num+=1
                            if message_num >= test_num:
                                break
                            time_wait = 20
                    for rcv_canfd_msgs in rcv_canfd_msgs:
                        if tx_msg.frame_id == rcv_canfd_msgs.frame.can_id:
                            rcv_canfd_list.append(rcv_canfd_msgs)
                            message_num+=1
                            if message_num >= test_num:
                                break
                            time_wait = 20
                            
                    if time_wait > 0:
                        time_wait -= 1
                        time.sleep(0.1)
                    else:
                        print("Get message:%s fail"%hex(tx_msg.frame_id))
                        break
    print("Record Messages Done")
    return rcv_can_list, rcv_canfd_list

class TC:
    def __init__(self, project):
        self.test_cnt = 0
        self.pass_cnt = 0
        self.fail_cnt = 0
        self.project = project

    def start_test(self, dbc_analyzer_obj, zcanlib, handle, chn_handle):
        dh1766setvolt(12,12,0)
        dh1766onall()
        time.sleep(1)
        self.t32 = t32_launch.T32_Launch()
        self.t32.t32api.T32_Cmd(b'SYStem.RESetTarget')
        time.sleep(1)
        self.t32.t32api.T32_Cmd(b'SYStem.Mode Attach')
        self.t32.t32api.T32_Cmd(b"go")

        if self.project == "E01":
            self.SYS_CoreRunCnt()
            self.SYS_CpuLoad()
            self.SYS_StackSize_e01()
            self.ASW_Version()
            self.t32.t32api.T32_Cmd(b"quit")
            dh1766offall()
            time.sleep(1)
            dh1766onall()
            time.sleep(2)
            all_can_list, all_canfd_list = get_all_msgs(dbc_analyzer_obj, zcanlib, chn_handle, TEST_NUM+1)
            self.period_check(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.dlc_check(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.unused_bit(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.crc_check_e01(dbc_analyzer_obj, all_can_list, all_canfd_list)
            print("\nDoIP Connect...")
            self.doip = DoIP()
            self.DCM_CommunicationControl(dbc_analyzer_obj, zcanlib, chn_handle)
            self.DCM_ReadDataByIdentifier_e01(dbc_analyzer_obj, zcanlib, chn_handle)
            self.NVM_VIN(dbc_analyzer_obj, zcanlib, chn_handle)
            chn_handle = self.NM_IDRange(dbc_analyzer_obj, zcanlib, handle, chn_handle)
        else:
            self.SYS_CoreRunCnt()
            self.SYS_CpuLoad()
            self.SYS_StackSize()
            self.ASW_Version()
            self.t32.t32api.T32_Cmd(b"quit")
            dh1766offall()
            time.sleep(1)
            dh1766onall()
            time.sleep(1)
            all_can_list, all_canfd_list = get_all_msgs(dbc_analyzer_obj, zcanlib, chn_handle, TEST_NUM+1)
            self.period_check(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.dlc_check(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.unused_bit(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.crc_check(dbc_analyzer_obj, all_can_list, all_canfd_list)
            self.DCM_CommunicationControl(dbc_analyzer_obj, zcanlib, chn_handle)
            self.DCM_ReadDataByIdentifier(dbc_analyzer_obj, zcanlib, chn_handle)
            self.NVM_VIN(dbc_analyzer_obj, zcanlib, chn_handle)
            chn_handle = self.NM_IDRange(dbc_analyzer_obj, zcanlib, handle, chn_handle)

        
        print("\nTest Result:")
        print("Total: %d\nPass: %d\nFail: %d"%(self.test_cnt,self.pass_cnt,self.fail_cnt))
        print("\nRun Testcase Finished")

        return chn_handle

    def ASW_Version(self):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("ASW Version Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: add variant")
        variant_list = [
            "AEB_Version",
            "HMI_Version",
            "ICAS_Version",
            "LAS_Version",
            "RLGS_Version",
            "TOS_Version",
            "VMC_Version",
            "VME_Version",
            "VMP_Version",
            "VAL_Version"
        ]
        #check variant
        for variant in variant_list:
            if self.t32.T32_GetSymbol(variant) == 0xffffffff:
                test_flg = 0
                print("Add Variant Fail")
        #Step 2
        if test_flg == 1:
            print("Add Variant Success")
            print("Step2: check ASW Version")
            value = []
            #read ASW Version
            for i in range(len(variant_list)):
                read_value, error = self.t32.T32_ReadValue(variant_list[i])
                if error != 0:
                    test_flg = 0
                value.append(read_value)
                print("%s: %d"%(variant_list[i],value[i]))
            if test_flg != 1:
                print("Read ASW Version Err")

        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("ASW Version Test Pass")
        else:
            self.fail_cnt += 1
            print("ASW Version Test Fail")
        print("ASW Version Test Done")

    def SYS_StackSize_e01(self):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("Stack Size Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: add variant")
        variant = "StackMonr_stStackSize"
        element = [
            "u8Core0_App_100ms",
            "u8Core0_App_10ms",
            "u8Core0_App_20ms",
            "u8Core0_App_500ms",
            "u8Core0_App_50ms",
            "u8Core0_App_5ms",
            "u8Core0_Bsw_10ms",
            "u8Core0_Bsw_1ms",
            "u8Core0_Bsw_20ms",
            "u8Core0_Bsw_5ms",
            "u8Core0_Swc_Init",
            "u8Core1_Aeb_20ms",
            "u8Core1_App_100ms",
            "u8Core1_App_10ms",
            "u8Core1_App_20ms",
            "u8Core1_App_40ms",
            "u8Core1_Bsw_10ms",
            "u8Core1_Swc_Init",
            "u8Core2_App_10ms",
            "u8Core2_App_40ms",
            "u8Core2_App_50ms",
            "u8Core2_BSW_30ms",
            "u8Core2_BSW_50ms",
            "u8Core2_Bsw_10ms",
            "u8Core2_Swc_Init",
            "u8Core3_Bsw_10ms",
            "u8Core3_Bsw_5ms",
            "u8Core3_Swc_Init",
            "u8Default_Init_Task",
            "u8Default_Init_Task_Core1",
            "u8Default_Init_Task_Core1_Trusted",
            "u8Default_Init_Task_Core2",
            "u8Default_Init_Task_Core2_Trusted",
            "u8Default_Init_Task_Core3",
            "u8Default_Init_Task_Core3_Trusted",
            "u8Default_Init_Task_Trusted",
            "u8IdleTask_OsCore0",
            "u8IdleTask_OsCore1",
            "u8IdleTask_OsCore2",
            "u8IdleTask_OsCore3",
        ]
        #check variant
        if self.t32.T32_GetSymbol(variant) != 0xffffffff:
            print("Add Variant Success")
        else:
            test_flg = 0
            print("Add Variant Fail")
        #Step 2
        if test_flg == 1:
            print("Step2: wait 2s")
            time.sleep(2)
        #Step 3
        if test_flg == 1:
            print("Step3: check stack size")
            value = []
            #read stack size
            print("Max Used Stack Size:")
            for i in range(len(element)):
                read_value, error = self.t32.T32_ReadValue(variant+"."+element[i])
                if error != 0:
                    test_flg = 0
                value.append(read_value)
                print("%s: %d%%"%(element[i],value[i]))
            if test_flg != 1:
                print("Read Stack Size Err")
            #check cpu load
            if test_flg == 1:
                for i in range(len(element)):
                    if value[i] > 90:
                        test_flg = 0
                        print("Stack Size Err")
                        break

        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("Stack Size Test Pass")
        else:
            self.fail_cnt += 1
            print("Stack Size Test Fail")
        print("Stack Size Test Done")

    def SYS_StackSize(self):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("Stack Size Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: add variant")
        variant = "StackMonr_stStackSize"
        element = [
            "u8Core0_App_100ms",
            "u8Core0_App_10ms",
            "u8Core0_App_20ms",
            "u8Core0_App_500ms",
            "u8Core0_App_50ms",
            "u8Core0_App_5ms",
            "u8Core0_Bsw_10ms",
            "u8Core0_Bsw_1ms",
            "u8Core0_Bsw_20ms",
            "u8Core0_Bsw_5ms",
            "u8Core0_Swc_Init",
            "u8Core1_Aeb_20ms",
            "u8Core1_App_100ms",
            "u8Core1_App_10ms",
            "u8Core1_App_20ms",
            "u8Core1_App_40ms",
            "u8Core1_Bsw_10ms",
            "u8Core1_Swc_Init",
            "u8Core2_App_10ms",
            "u8Core2_App_40ms",
            "u8Core2_App_50ms",
            "u8Core2_BSW_30ms",
            "u8Core2_BSW_50ms",
            "u8Core2_Bsw_10ms",
            "u8Core2_Swc_Init",
            "u8Core3_Bsw_10ms",
            "u8Core3_Bsw_5ms",
            "u8Core3_Swc_15ms",
            "u8Core3_Swc_5ms",
            "u8Core3_Swc_Init",
            "u8Core3_VeCtrl_10ms",
            "u8Default_Init_Task",
            "u8Default_Init_Task_Core1",
            "u8Default_Init_Task_Core1_Trusted",
            "u8Default_Init_Task_Core2",
            "u8Default_Init_Task_Core2_Trusted",
            "u8Default_Init_Task_Core3",
            "u8Default_Init_Task_Core3_Trusted",
            "u8Default_Init_Task_Trusted",
            "u8IdleTask_OsCore0",
            "u8IdleTask_OsCore1",
            "u8IdleTask_OsCore2",
            "u8IdleTask_OsCore3",
            "u8OsTask_SWC_USS",
            "u8TSK_Uss_Data_Processing_50ms",
            "u8TSK_Uss_Perception_40ms",
        ]
        #check variant
        if self.t32.T32_GetSymbol(variant) != 0xffffffff:
            print("Add Variant Success")
        else:
            test_flg = 0
            print("Add Variant Fail")
        #Step 2
        if test_flg == 1:
            print("Step2: wait 2s")
            time.sleep(2)
        #Step 3
        if test_flg == 1:
            print("Step3: check stack size")
            value = []
            #read stack size
            print("Max Used Stack Size:")
            for i in range(len(element)):
                read_value, error = self.t32.T32_ReadValue(variant+"."+element[i])
                if error != 0:
                    test_flg = 0
                value.append(read_value)
                print("%s: %d%%"%(element[i],value[i]))
            if test_flg != 1:
                print("Read Stack Size Err")
            #check cpu load
            if test_flg == 1:
                for i in range(len(element)):
                    if value[i] > 90:
                        test_flg = 0
                        print("Stack Size Err")
                        break

        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("Stack Size Test Pass")
        else:
            self.fail_cnt += 1
            print("Stack Size Test Fail")
        print("Stack Size Test Done")

    def SYS_CpuLoad(self):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CPU Load Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: add variant")
        variant = "RTM_CPU_Load"
        #check variant
        if self.t32.T32_GetSymbol(variant) != 0xffffffff:
            print("Add Variant Success")
        else:
            test_flg = 0
            print("Add Variant Fail")
        #Step 2
        if test_flg == 1:
            print("Step2: wait 2s")
            time.sleep(2)
        #Step 3
        if test_flg == 1:
            print("Step3: check cpu load")
            value = []
            #read max cpu load
            print("Max CPU Load:")
            for i in range(4):
                read_value, error = self.t32.T32_ReadValue(variant+"["+str(i)+"].Max_Cpu_Load")
                if error != 0:
                    test_flg = 0
                value.append(read_value)
                print("Core%d: %d%%"%(i,value[i]))
            if test_flg != 1:
                print("Read CPU Load Err")
            #check cpu load
            if test_flg == 1:
                for i in range(4):
                    if value[i] > 80:
                        test_flg = 0
                        print("CPU Load Err")
                        break

        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("CPU Load Test Pass")
        else:
            self.fail_cnt += 1
            print("CPU Load Test Fail")
        print("CPU Load Test Done")

    def SYS_CoreRunCnt(self):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("Core Running Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: add variant")
        variant = "testCoreRunCnt"
        #check variant
        if self.t32.T32_GetSymbol(variant) != 0xffffffff:
            print("Add Variant Success")
        else:
            test_flg = 0
            print("Add Variant Fail")
        #Step 2
        if test_flg == 1:
            print("Step2: wait 1min")
            time.sleep(60)
        #Step 3
        if test_flg == 1:
            print("Step3: check variant value")
            time_wait = 20
            value_last = []
            while time_wait > 0 and test_flg == 1:
                value = []
                if len(value_last) > 0:
                    #read value
                    for i in range(4):
                        read_value, error = self.t32.T32_ReadValue(variant+"["+str(i)+"]")
                        if error != 0:
                            test_flg = 0
                        value.append(read_value)
                    if test_flg != 1:
                        print("Read CoreRunCnt Err")
                        break
                    #cal value range
                    if value[0] == 0x1:
                        value_range = [0xffff,0x1,0x2]
                    else:
                        value_range = [value[0]-1,value[0],(value[0]+1)%0xffff]
                    #check value consistency 
                    for i in range(3):
                        if value[i+1] not in value_range:
                            test_flg = 0
                            print("Err Value:",value)
                            break
                    #compare value 
                    if test_flg == 1:
                        value_temp =  value_last[0]-0xfff5 if (value_last[0]+10) > 0xffff else value_last[0]+10
                        if value_temp == 0x1:
                            value_range = [0xfffe,0xffff,0x1,0x2,0x3]
                        elif value_temp == 0x2:
                            value_range = [0xffff,0x1,0x2,0x3,0x4]
                        else:
                            value_range = [value_temp-2,value_temp-1,value_temp,(value_temp+1)%0xffff,(value_temp+2)%0xffff]
                        if value[0] not in value_range:
                            test_flg = 0
                            print("Value Change Err:")
                            print("Before 100ms:",value_last)
                            print("After 100ms:",value)
                            break
                    #restore calue
                    value_last = value
                else:
                    #read value
                    for i in range(4):
                        read_value, error = self.t32.T32_ReadValue(variant+"["+str(i)+"]")
                        if error != 0:
                            test_flg = 0
                        value_last.append(read_value)
                    if test_flg != 1:
                        print("Read CoreRunCnt Err")
                        break
                    #cal value range
                    if value_last[0] == 0x1:
                        value_range = [0xffff,0x1,0x2]
                    else:
                        value_range = [value_last[0]-1,value_last[0],(value_last[0]+1)%0xffff]
                    #check value consistency
                    for i in range(3):
                        if value_last[i+1] not in value_range:
                            test_flg = 0
                            print("Err Value:",value)
                            break
                time_wait -= 1
                time.sleep(0.1)
        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("Core Running Test Pass")
        else:
            self.fail_cnt += 1
            print("Core Running Test Fail")
        print("Core Running Test Done")

    def NM_IDRange(self, dbc_analyzer_obj, zcanlib, handle, chn_handle):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("NM IDRange Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: KL30 ON and KL15 OFF")
        dh1766setvolt(0,0,0)
        time.sleep(1)
        dh1766setvolt(12,0,0)
        print("Wait 5s")
        time.sleep(5)
        #PreCondition Check
        rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
        time.sleep(1)
        rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
        if len(rcv_can_msgs) > 0 or len(rcv_canfd_msgs) > 0:
            test_flg = 0
            print("PreCondition check fail")
        else:
            print("PreCondition check success")
        #Step 1
        if test_flg == 1:
            print("Step1: send NM message:id=0x600,dlc=1")
            can_id = 0x600
            period = 300    #ms
            dlc = 1
            data = [0x0]
            chn_handle = zcanlib.auto_start(handle, chn_handle, can_id, dlc, period, data)
        #Step 2
        if test_flg == 1:
            print("Step2: check network status")
            test_flg = msg_check(dbc_analyzer_obj, zcanlib, chn_handle)
            if test_flg == 0:
                print("Network wakeup fail")
            else:
                print("Network wakeup success")
        #Step 3
        if test_flg == 1:
            print("Step3: stop NM message")
            chn_handle = zcanlib.canfd_start(handle, 0)
            print("Wait 5s")
            time.sleep(5)
        #Step 4
        if test_flg == 1:
            print("Step4: check network status")
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            time.sleep(1)
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            if len(rcv_can_msgs) > 0 or len(rcv_canfd_msgs) > 0:
                test_flg = 0
                print("Network sleep fail")
            else:
                print("Network sleep success")
        #Step 5
        if test_flg == 1:
            print("Step5: send NM message:id=0x67F,dlc=8")
            can_id = 0x67F
            period = 300    #ms
            dlc = 8
            data = [0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0]
            chn_handle = zcanlib.auto_start(handle, chn_handle, can_id, dlc, period, data)
        #Step 6
        if test_flg == 1:
            print("Step6: check network status")
            test_flg = msg_check(dbc_analyzer_obj, zcanlib, chn_handle)
            if test_flg == 0:
                print("Network wakeup fail")
            else:
                print("Network wakeup success")
        #Step 7
        if test_flg == 1:
            print("Step7: stop NM message")
            chn_handle = zcanlib.canfd_start(handle, 0)
            print("Wait 5s")
            time.sleep(5)
        #Step 8
        if test_flg == 1:
            print("Step8: check network status")
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            time.sleep(1)
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            if len(rcv_can_msgs) > 0 or len(rcv_canfd_msgs) > 0:
                test_flg = 0
                print("Network sleep fail")
            else:
                print("Network sleep success")
        #PreCondition Reset
        print("PreCondition Reset: KL30 ON and KL15 ON")
        dh1766setvolt(12,12,0)
        print("Wait 2s")

        if test_flg == 1:
            self.pass_cnt += 1
            print("NM IDRange Test Pass")
        else:
            self.fail_cnt += 1
            print("NM IDRange Test Fail")
        print("NM IDRange Test Done")

        return chn_handle

    def NVM_VIN(self, dbc_analyzer_obj, zcanlib, chn_handle):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("NVM VIN Code Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: send 10 03")
        response = self.doip.client.change_session(0x03)
        res_act = response.get_payload().hex()
        res_exp = "5003003201f4"
        if res_exp != res_act:
            test_flg = 0
        # req_data = [0x10,0x03]
        # res_data = [0x50,0x03,0x00,0x32,0x01,0xF4]
        # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 2
        if test_flg == 1:
            print("Step2: send 27 01/02 to unlock")
            response = self.doip.client.unlock_security_access(0x01)
            res_act = response.get_payload().hex()
            res_exp = "6702"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x27,0x03]
            # res_list,test_flg = get_response(zcanlib,chn_handle,req_data,self.project)
        # if test_flg == 1:
        #     seed = ''.join(hex(res_list[i+1])[2:].zfill(2) for i in range(4))
        #     key = unlock(seed)
        #     # print(key)
        #     req_data = [0x27,0x04]
        #     for i in range(4):
        #         req_data.append(int(key[i*2:i*2+2],16))
        #     res_data = [0x67,0x04]
        #     test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 3
        if test_flg == 1:
            print("Step3: send 2E F1 90 01*17")
            response = self.doip.client.write_data_by_identifier(0xF190,"0101010101010101010101010101010101")
            res_act = response.get_payload().hex()
            res_exp = "6ef190"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x2E,0xF1,0x90,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01]
            # res_data = [0x6E,0xF1,0x90]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 4
        if test_flg == 1:
            print("Step4: send 22 F1 90")
            response = self.doip.client.read_data_by_identifier(0xF190)
            res_act = response.get_payload().hex()
            res_exp = "62f1900101010101010101010101010101010101"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x22,0xF1,0x90]
            # res_data = [0x62,0xF1,0x90,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 5
        if test_flg == 1:
            print("Step5: Battery off and on")
            dh1766setvolt(12,0,0)
            time.sleep(5)
            dh1766setvolt(12,12,0)
            time.sleep(1)
        #Step 6
        if test_flg == 1:
            print("Step6: send 22 F1 90")
            response = self.doip.client.read_data_by_identifier(0xF190)
            res_act = response.get_payload().hex()
            res_exp = "62f1900101010101010101010101010101010101"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x22,0xF1,0x90]
            # res_data = [0x62,0xF1,0x90,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 7
        if test_flg == 1:
            print("Step7: send 10 03")
            response = self.doip.client.change_session(0x03)
            res_act = response.get_payload().hex()
            res_exp = "5003003201f4"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x10,0x03]
            # res_data = [0x50,0x03,0x00,0x32,0x01,0xF4]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 8
        if test_flg == 1:
            print("Step8: send 27 01/02 to unlock")
            response = self.doip.client.unlock_security_access(0x01)
            res_act = response.get_payload().hex()
            res_exp = "6702"
            if res_exp != res_act:
                test_flg = 0
        #     req_data = [0x27,0x03]
        #     res_list,test_flg = get_response(zcanlib,chn_handle,req_data,self.project)
        # if test_flg == 1:
        #     seed = ''.join(hex(res_list[i+1])[2:].zfill(2) for i in range(4))
        #     key = unlock(seed)
        #     # print(key)
        #     req_data = [0x27,0x04]
        #     for i in range(4):
        #         req_data.append(int(key[i*2:i*2+2],16))
        #     res_data = [0x67,0x04]
        #     test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 9
        if test_flg == 1:
            print("Step9: send 2E F1 90 02*17")
            response = self.doip.client.write_data_by_identifier(0xF190,"0202020202020202020202020202020202")
            res_act = response.get_payload().hex()
            res_exp = "6ef190"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x2E,0xF1,0x90,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02]
            # res_data = [0x6E,0xF1,0x90]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 10
        if test_flg == 1:
            print("Step10: send 22 F1 90")
            response = self.doip.client.read_data_by_identifier(0xF190)
            res_act = response.get_payload().hex()
            res_exp = "62f1900202020202020202020202020202020202"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x22,0xF1,0x90]
            # res_data = [0x62,0xF1,0x90,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 11
        if test_flg == 1:
            print("Step11: Battery off and on")
            dh1766setvolt(12,0,0)
            time.sleep(5)
            dh1766setvolt(12,12,0)
            time.sleep(1)
        #Step 12
        if test_flg == 1:
            print("Step12: send 22 F1 90")
            response = self.doip.client.read_data_by_identifier(0xF190)
            res_act = response.get_payload().hex()
            res_exp = "62f1900202020202020202020202020202020202"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x22,0xF1,0x90]
            # res_data = [0x62,0xF1,0x90,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("NVM VIN Code Test Pass")
        else:
            self.fail_cnt += 1
            print("NVM VIN Code Test Fail")
        print("NVM VIN Code Test Done")

    def DCM_ReadDataByIdentifier_e01(self, dbc_analyzer_obj, zcanlib, chn_handle):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("DCM ReadDataByIdentifier Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: send 22 F1 89 to read Vehicle Manufacturer ECU version")
        response = self.doip.client.read_data_by_identifier(0xF189)
        res_act = response.get_payload().hex()
        if "62" == res_act[0:2]:
            res_list = [res_act[i*2+6:i*2+8] for i in range(int(len(res_act)/2)-3)]
            print("Version is:",''.join(chr(int(i,16)) for i in res_list))
        else:
            test_flg = 0
        # req_data = [0x22,0xF1,0x89]
        # test_flg = read_version(zcanlib, chn_handle, req_data, self.project)
        #Step 2
        if test_flg == 1:
            print("Step2: send 22 F1 95 to read System Supplier ECU version")
            response = self.doip.client.read_data_by_identifier(0xF195)
            res_act = response.get_payload().hex()
            if "62" == res_act[0:2]:
                res_list = [res_act[i*2+6:i*2+8] for i in range(int(len(res_act)/2)-3)]
                print("Version is:",''.join(chr(int(i,16)) for i in res_list))
            else:
                test_flg = 0
        #Step 3
        if test_flg == 1:
            print("Step3: send 22 F0 32 to read cal version")
            response = self.doip.client.read_data_by_identifier(0xF032)
            res_act = response.get_payload().hex()
            if "62" == res_act[0:2]:
                res_list = [res_act[i*2+6:i*2+8] for i in range(int(len(res_act)/2)-3)]
                print("Version is:",''.join(chr(int(i,16)) for i in res_list))
            else:
                test_flg = 0
            # req_data = [0x22,0xF0,0x32]
            # test_flg = read_version(zcanlib, chn_handle, req_data, self.project)
        #Step 4
        if test_flg == 1:
            print("Step4: send 10 03")
            response = self.doip.client.change_session(0x03)
            res_act = response.get_payload().hex()
            res_exp = "5003003201f4"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x10,0x03]
            # res_data = [0x50,0x03,0x00,0x32,0x01,0xF4]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 5
        if test_flg == 1:
            print("Step5: send 31 01 02 03")
            response = self.doip.client.start_routine(0x0203)
            res_act = response.get_payload().hex()
            if "71" != res_act[0:2]:
                test_flg = 0
            # req_data = [0x31,0x01,0x02,0x03]
            # res_data = [0x71,0x01,0x02,0x03,0x00]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 6
        if test_flg == 1:
            print("Step6: send 10 02")
            response = self.doip.client.change_session(0x02)
            res_act = response.get_payload().hex()
            res_exp = "5002003201f4"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x10,0x02]
            # res_data = [0x50,0x02,0x00,0x32,0x01,0xF4]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 7
        if test_flg == 1:
            print("Step7: send 22 F1 80 to read boot version")
            response = self.doip.client.read_data_by_identifier(0xF180)
            res_act = response.get_payload().hex()
            if "62" == res_act[0:2]:
                res_list = [res_act[i*2+6:i*2+8] for i in range(int(len(res_act)/2)-3)]
                print("Version is:",''.join(chr(int(i,16)) for i in res_list))
            else:
                test_flg = 0
            # req_data = [0x22,0xF1,0x80]
            # test_flg = read_version(zcanlib, chn_handle, req_data, self.project)
        #PreCondition Reset
        if test_flg == 1:
            print("PreCondition Reset: Enter default session")
            response = self.doip.client.change_session(0x01)
            res_act = response.get_payload().hex()
            res_exp = "5001003201f4"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x10,0x01]
            # res_data = [0x50,0x01,0x00,0x32,0x01,0xF4]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)

        if test_flg == 1:
            self.pass_cnt += 1
            print("DCM ReadDataByIdentifier Test Pass")
        else:
            self.fail_cnt += 1
            print("DCM ReadDataByIdentifier Test Fail")
        print("DCM ReadDataByIdentifier Test Done")

    def DCM_ReadDataByIdentifier(self, dbc_analyzer_obj, zcanlib, chn_handle):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("DCM ReadDataByIdentifier Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: send 22 F1 88 to read sw version")
        req_data = [0x22,0xF1,0x88]
        read_version(zcanlib, chn_handle, req_data, self.project)
        #Step 2
        if test_flg == 1:
            print("Step2: send 22 F0 32 to read cal version")
            req_data = [0x22,0xF0,0x32]
            read_version(zcanlib, chn_handle, req_data, self.project)
        #Step 3
        if test_flg == 1:
            print("Step3: send 10 03")
            req_data = [0x10,0x03]
            res_data = [0x50,0x03,0x00,0x32,0x01,0xF4]
            test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 4
        if test_flg == 1:
            print("Step4: send 31 01 D0 03")
            req_data = [0x31,0x01,0xD0,0x03]
            res_data = [0x71,0x01,0xD0,0x03,0x00]
            test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 5
        if test_flg == 1:
            print("Step5: send 10 02")
            req_data = [0x10,0x02]
            res_data = [0x50,0x02,0x00,0x32,0x01,0xF4]
            test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 6
        if test_flg == 1:
            print("Step6: send 22 F1 80 to read boot version")
            req_data = [0x22,0xF1,0x80]
            read_version(zcanlib, chn_handle, req_data, self.project)
        #PreCondition Reset
        if test_flg == 1:
            print("PreCondition Reset: Enter default session")
            req_data = [0x10,0x01]
            res_data = [0x50,0x01,0x00,0x32,0x01,0xF4]
            test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)

        if test_flg == 1:
            self.pass_cnt += 1
            print("DCM ReadDataByIdentifier Test Pass")
        else:
            self.fail_cnt += 1
            print("DCM ReadDataByIdentifier Test Fail")
        print("DCM ReadDataByIdentifier Test Done")

    def DCM_CommunicationControl(self, dbc_analyzer_obj, zcanlib, chn_handle):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("DCM CommunicationControl Test Start...")
        test_flg = 1  #0-fail 1-pass
        #PreCondition Set
        print("PreCondition Set: None")
        #Step 1
        print("Step1: send 10 03")
        response = self.doip.client.change_session(0x03)
        res_act = response.get_payload().hex()
        res_exp = "5003003201f4"
        if res_exp != res_act:
            test_flg = 0
        # req_data = [0x10,0x03]
        # res_data = [0x50,0x03,0x00,0x32,0x01,0xF4]
        # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 2
        if test_flg == 1:
            print("Step2: send 28 03 03")
            response = self.doip.client.communication_control(0x03,0x03)
            res_act = response.get_payload().hex()
            res_exp = "6803"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x28,0x03,0x03]
            # res_data = [0x68,0x03]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 3
        if test_flg == 1:
            print("Step3: check tx message")
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            time.sleep(1)
            rcv_can_msgs, rcv_canfd_msgs = zcanlib.can_receive(chn_handle)
            if len(rcv_can_msgs) > 0 or len(rcv_canfd_msgs) > 0:
                test_flg = 0
                print("Stop communication fail")
            else:
                print("Stop communication success")
        #Step 4
        if test_flg == 1:
            print("Step4: send 28 00 03")
            response = self.doip.client.communication_control(0x00,0x03)
            res_act = response.get_payload().hex()
            res_exp = "6800"
            if res_exp != res_act:
                test_flg = 0
            # req_data = [0x28,0x00,0x03]
            # res_data = [0x68,0x00]
            # test_flg = res_check(zcanlib,chn_handle,req_data,res_data,self.project)
        #Step 5
        if test_flg == 1:
            print("Step5: check tx message")
            test_flg = msg_check(dbc_analyzer_obj, zcanlib, chn_handle)
            if test_flg == 0:
                print("Start communication fail")
            else:
                print("Start communication success")
        #PreCondition Reset
        print("PreCondition Reset: None")

        if test_flg == 1:
            self.pass_cnt += 1
            print("DCM CommunicationControl Test Pass")
        else:
            self.fail_cnt += 1
            print("DCM CommunicationControl Test Fail")
        print("DCM CommunicationControl Test Done")

    def crc_check_e01(self, dbc_analyzer_obj, all_can_list, all_canfd_list):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CANTx Cnt&CRC Test Start...")
        test_cnt = 0
        pass_cnt = 0
        fail_cnt = 0
        for channel_obj in dbc_analyzer_obj.channel_obj_list:
            print("Channel_Name:",channel_obj.channel_name)
            for tx_msg in channel_obj.tx_msg_list:
                if tx_msg.send_type == 'Cyclic':
                    test_cnt += 1
                    print("Message Name: %s" %tx_msg.name,)
                    print("Message Id: 0x%x" %tx_msg.frame_id)

                    cnt_flag = 0
                    crc_flag = 0
                    cnt_bit = []
                    crc_bit = []
                    cnt_len = []
                    crc_len = []
                    dataid = []
                    for signal in tx_msg.signals:
                        if "Rolling message counter" in str(signal.comment):
                            cnt_flag = 1
                            cnt_bit.append(signal.start)
                            cnt_len.append(signal.length)
                        if "CRC (SAE J1850 CRC-8)" in str(signal.comment):
                            crc_flag = 1
                            crc_bit.append(signal.start)
                            crc_len.append(signal.length)
                            if "DataID:0x" in str(signal.comment):
                                dataid.append(str(signal.comment).split("DataID:0x")[1])

                    if cnt_flag == 1 and crc_flag == 1 and len(cnt_bit) == len(crc_bit) and len(cnt_bit) == len(dataid):
                        print("Support Cnt&CRC")
                        #get tx messages
                        rcv_can_list, rcv_canfd_list = get_msgs(all_can_list, all_canfd_list, tx_msg, TEST_NUM)

                        if len(rcv_can_list)+len(rcv_canfd_list) < TEST_NUM:
                            fail_cnt += 1
                            print("Get Frame error")
                            print("Cnt&CRC Test Fail\n")
                            continue

                        for k in range(len(cnt_bit)):
                            cnt_err_cnt = 0
                            crc_err_cnt = 0
                            if cnt_len[k] == 4 and crc_len[k] == 8:
                                cnt_byte = cnt_bit[k]//8
                                crc_byte = crc_bit[k]//8
                            else:
                                cnt_err_cnt += 1
                                print("Get CRC Bit Info error")
                                print("Cnt&CRC Test Fail\n")
                                break

                            for i in range(len(rcv_can_list)):
                                rcv_msg = rcv_can_list[i]
                                if cnt_bit[k]%8 >= 4:
                                    cnt_new = (rcv_msg.frame.data[cnt_byte]&0xF0)>>4
                                else:
                                    cnt_new = (rcv_msg.frame.data[cnt_byte]&0x0F)
                                crc_new = rcv_msg.frame.data[crc_byte]
                                crc_data = []
                                crc_data.append(int(dataid[k][2:4],16))
                                crc_data.append(int(dataid[k][0:2],16))
                                for idx in range(rcv_msg.frame.can_dlc):
                                    if idx > crc_byte and idx < crc_byte+8:
                                        crc_data.append(rcv_msg.frame.data[idx])
                                #cnt check
                                if i == 0:
                                    cnt_las = cnt_new
                                else:
                                    if cnt_las > 0xD:
                                        cnt_las = 0
                                    else:
                                        cnt_las += 1
                                    if cnt_las&0x0F != cnt_new:
                                        cnt_err_cnt += 1
                                        print("AliveCounter Err Frame:")
                                        for j in range(rcv_msg.frame.can_dlc):
                                            print("%02x " % rcv_msg.frame.data[j], end='')
                                        print("")
                                    cnt_las = cnt_new
                                #crc check
                                crc_cal = crclib_getCRC8(crc_data, len(crc_data), 0x0)
                                if crc_cal != crc_new:
                                    crc_err_cnt += 1
                                    print("CRC Err Frame:")
                                    for j in range(rcv_msg.frame.can_dlc):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")
                            for i in range(len(rcv_canfd_list)):
                                rcv_msg = rcv_canfd_list[i]
                                if cnt_bit[k]%8 >= 4:
                                    cnt_new = (rcv_msg.frame.data[cnt_byte]&0xF0)>>4
                                else:
                                    cnt_new = (rcv_msg.frame.data[cnt_byte]&0x0F)
                                crc_new = rcv_msg.frame.data[crc_byte]
                                crc_data = []
                                crc_data.append(int(dataid[k][2:4],16))
                                crc_data.append(int(dataid[k][0:2],16))
                                for idx in range(rcv_msg.frame.len):
                                    if idx > crc_byte and idx < crc_byte+8:
                                        crc_data.append(rcv_msg.frame.data[idx])
                                #cnt check
                                if i == 0:
                                    cnt_las = cnt_new
                                else:
                                    if cnt_las > 0xD:
                                        cnt_las = 0
                                    else:
                                        cnt_las += 1
                                    if cnt_las&0x0F != cnt_new:
                                        cnt_err_cnt += 1
                                        print("AliveCounter Err Frame:")
                                        for j in range(rcv_msg.frame.len):
                                            print("%02x " % rcv_msg.frame.data[j], end='')
                                        print("")
                                    cnt_las = cnt_new
                                #crc check
                                crc_cal = crclib_getCRC8(crc_data, len(crc_data), 0x0)
                                if crc_cal != crc_new:
                                    crc_err_cnt += 1
                                    print("CRC Err Frame:")
                                    for j in range(rcv_msg.frame.len):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")

                        print("Number Of Frame:",TEST_NUM)
                        if cnt_err_cnt > 0 or crc_err_cnt > 0:
                            fail_cnt += 1
                            if cnt_err_cnt > 0:
                                print("AliveCounter Err Cnt:",cnt_err_cnt)
                            if crc_err_cnt > 0:
                                print("CRC Err Cnt:",crc_err_cnt)
                            print("Cnt&CRC Test Fail\n")
                        else:
                            pass_cnt += 1
                            print("Cnt&CRC Test Pass\n")
                    elif cnt_flag == 0 and crc_flag == 0:
                        print("Unsupport Cnt&CRC\n")
                    else:
                        fail_cnt += 1
                        print("Get Cnt&CRC Info error")
                        print("Cnt&CRC Test Fail\n")

        print("Total Message:",test_cnt)
        print("Pass:",pass_cnt)
        print("Fail:",fail_cnt)
        print("NA:",test_cnt-pass_cnt-fail_cnt)
        if fail_cnt > 0:
            self.fail_cnt += 1
            print("CANTx Cnt&CRC Test Fail")
        else:
            self.pass_cnt += 1
            print("CANTx Cnt&CRC Test Pass")
        print("CANTx Cnt&CRC Test Done")

    def crc_check(self, dbc_analyzer_obj, all_can_list, all_canfd_list):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CANTx Cnt&CRC Test Start...")
        test_cnt = 0
        pass_cnt = 0
        fail_cnt = 0
        for channel_obj in dbc_analyzer_obj.channel_obj_list:
            print("Channel_Name:",channel_obj.channel_name)
            for tx_msg in channel_obj.tx_msg_list:
                if tx_msg.send_type == 'Cyclic':
                    test_cnt += 1
                    print("Message Name: %s" %tx_msg.name,)
                    print("Message Id: 0x%x" %tx_msg.frame_id)

                    cnt_flag = 0
                    crc_flag = 0
                    for signal in tx_msg.signals:
                        if "Rolling message counter" in str(signal.comment):
                            cnt_flag = 1
                            cnt_bit = signal.start
                            cnt_len = signal.length
                        if "CRC (SAE J1850 CRC-8)" in str(signal.comment):
                            crc_flag = 1
                            crc_bit = signal.start
                            crc_len = signal.length

                    if cnt_flag == 1 and crc_flag == 1:
                        print("Support Cnt&CRC")
                        if cnt_len == 4 and crc_len == 8:
                            cnt_byte = cnt_bit//8
                            crc_byte = crc_bit//8
                        else:
                            fail_cnt += 1
                            print("Get CRC Bit Info error")
                            print("Cnt&CRC Test Fail\n")
                            continue
                        
                        #get tx messages
                        rcv_can_list, rcv_canfd_list = get_msgs(all_can_list, all_canfd_list, tx_msg, TEST_NUM)

                        if len(rcv_can_list)+len(rcv_canfd_list) < TEST_NUM:
                            fail_cnt += 1
                            print("Get Frame error")
                            print("Cnt&CRC Test Fail\n")
                            continue

                        cnt_err_cnt = 0
                        crc_err_cnt = 0
                        for i in range(len(rcv_can_list)):
                            rcv_msg = rcv_can_list[i]
                            if cnt_bit%8 >= 4:
                                cnt_new = (rcv_msg.frame.data[cnt_byte]&0xF0)>>4
                            else:
                                cnt_new = (rcv_msg.frame.data[cnt_byte]&0x0F)
                            crc_new = rcv_msg.frame.data[crc_byte]
                            crc_data = []
                            for idx in range(rcv_msg.frame.can_dlc):
                                if idx != crc_byte:
                                    crc_data.append(rcv_msg.frame.data[idx])
                            #cnt check
                            if i == 0:
                                cnt_las = cnt_new
                            else:
                                if (cnt_las+1)&0x0F != cnt_new:
                                    cnt_err_cnt += 1
                                    print("AliveCounter Err Frame:")
                                    for j in range(rcv_msg.frame.can_dlc):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")
                                cnt_las = cnt_new
                            #crc check
                            crc_cal = crclib_getCRC8(crc_data, len(crc_data), 0xFF)
                            if crc_cal != crc_new:
                                crc_err_cnt += 1
                                print("CRC Err Frame:")
                                for j in range(rcv_msg.frame.can_dlc):
                                    print("%02x " % rcv_msg.frame.data[j], end='')
                                print("")
                        for i in range(len(rcv_canfd_list)):
                            rcv_msg = rcv_canfd_list[i]
                            if cnt_bit%8 >= 4:
                                cnt_new = (rcv_msg.frame.data[cnt_byte]&0xF0)>>4
                            else:
                                cnt_new = (rcv_msg.frame.data[cnt_byte]&0x0F)
                            crc_new = rcv_msg.frame.data[crc_byte]
                            crc_data = []
                            for idx in range(rcv_msg.frame.len):
                                if idx != crc_byte:
                                    crc_data.append(rcv_msg.frame.data[idx])
                            #cnt check
                            if i == 0:
                                cnt_las = cnt_new
                            else:
                                if (cnt_las+1)&0x0F != cnt_new:
                                    cnt_err_cnt += 1
                                    print("AliveCounter Err Frame:")
                                    for j in range(rcv_msg.frame.len):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")
                                cnt_las = cnt_new
                            #crc check
                            crc_cal = crclib_getCRC8(crc_data, len(crc_data), 0xFF)
                            if crc_cal != crc_new:
                                crc_err_cnt += 1
                                print("CRC Err Frame:")
                                for j in range(rcv_msg.frame.len):
                                    print("%02x " % rcv_msg.frame.data[j], end='')
                                print("")

                        print("Number Of Frame:",TEST_NUM)
                        if cnt_err_cnt > 0 or crc_err_cnt > 0:
                            fail_cnt += 1
                            if cnt_err_cnt > 0:
                                print("AliveCounter Err Cnt:",cnt_err_cnt)
                            if crc_err_cnt > 0:
                                print("CRC Err Cnt:",crc_err_cnt)
                            print("Cnt&CRC Test Fail\n")
                        else:
                            pass_cnt += 1
                            print("Cnt&CRC Test Pass\n")
                    elif cnt_flag == 0 and crc_flag == 0:
                        print("Unsupport Cnt&CRC\n")
                    else:
                        fail_cnt += 1
                        print("Get Cnt&CRC Info error")
                        print("Cnt&CRC Test Fail\n")

        print("Total Message:",test_cnt)
        print("Pass:",pass_cnt)
        print("Fail:",fail_cnt)
        print("NA:",test_cnt-pass_cnt-fail_cnt)
        if fail_cnt > 0:
            self.fail_cnt += 1
            print("CANTx Cnt&CRC Test Fail")
        else:
            self.pass_cnt += 1
            print("CANTx Cnt&CRC Test Pass")
        print("CANTx Cnt&CRC Test Done")

    def unused_bit(self, dbc_analyzer_obj, all_can_list, all_canfd_list):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CANTx Unused Bit Test Start...")
        test_cnt = 0
        pass_cnt = 0
        fail_cnt = 0
        for channel_obj in dbc_analyzer_obj.channel_obj_list:
            print("Channel_Name:",channel_obj.channel_name)
            for tx_msg in channel_obj.tx_msg_list:
                if tx_msg.send_type == 'Cyclic':
                    err_cnt = 0
                    test_cnt += 1
                    print("Message Name: %s" %tx_msg.name,)
                    print("Message Id: 0x%x" %tx_msg.frame_id)

                    duplicate_bit = 0
                    used_bit = set()
                    for signal in tx_msg.signals:
                        for i in range(signal.length):
                            if signal.byte_order == 'big_endian':
                                bit_value = signal.start-i+((8-(signal.start%8+1)+i)//8)*8*2
                            else:
                                bit_value = signal.start+i
                            if bit_value in used_bit:
                                print("Duplicate bit!!!:",bit_value)
                                duplicate_bit = 1
                            else:
                                used_bit.add(bit_value)
                    if duplicate_bit == 1:
                        fail_cnt += 1
                        print("Duplicate Bit error")
                        print("Unused Bit Test Fail\n")
                        continue
                    #get tx messages
                    rcv_can_list, rcv_canfd_list = get_msgs(all_can_list, all_canfd_list, tx_msg, TEST_NUM)

                    if len(rcv_can_list)+len(rcv_canfd_list) < TEST_NUM:
                        fail_cnt += 1
                        print("Get Frame error")
                        print("Unused Bit Test Fail\n")
                        continue
                    
                    for rcv_msg in rcv_can_list:
                        for i in range(8*rcv_msg.frame.can_dlc):
                            if i not in used_bit:
                                if rcv_msg.frame.data[i//8]&(1<<i%8) != UNUSEd_BIT_PATTERN:
                                    err_cnt+=1
                                    print("Unused Bit Err Frame:")
                                    for j in range(rcv_msg.frame.can_dlc):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")
                                    break
                    for rcv_msg in rcv_canfd_list:
                        for i in range(8*rcv_msg.frame.len):
                            if i not in used_bit:
                                if rcv_msg.frame.data[i//8]&(1<<i%8) != UNUSEd_BIT_PATTERN:
                                    err_cnt+=1
                                    print("Unused Bit Err Frame:")
                                    for j in range(rcv_msg.frame.len):
                                        print("%02x " % rcv_msg.frame.data[j], end='')
                                    print("")
                                    break

                    print("Number Of Frame:",TEST_NUM)
                    if err_cnt > 0:
                        print("Unused Bit Err Cnt:",err_cnt)
                        fail_cnt += 1
                        print("Unused Bit Test Fail\n")
                    else:
                        pass_cnt += 1
                        print("Unused Bit Test Pass\n")
        print("Total Message:",test_cnt)
        print("Pass:",pass_cnt)
        print("Fail:",fail_cnt)
        print("NA:",test_cnt-pass_cnt-fail_cnt)
        if fail_cnt > 0:
            self.fail_cnt += 1
            print("CANTx Unused Bit Test Fail")
        else:
            self.pass_cnt += 1
            print("CANTx Unused Bit Test Pass")
        print("CANTx Unused Bit Test Done")

    def dlc_check(self, dbc_analyzer_obj, all_can_list, all_canfd_list):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CANTx DLC Test Start...")
        test_cnt = 0
        pass_cnt = 0
        fail_cnt = 0
        for channel_obj in dbc_analyzer_obj.channel_obj_list:
            print("Channel_Name:",channel_obj.channel_name)
            for tx_msg in channel_obj.tx_msg_list:
                if tx_msg.send_type == 'Cyclic':
                    tx_msg_dlc_list = []# ms
                    err_cnt = 0
                    test_cnt += 1
                    print("Message Name: %s" %tx_msg.name,)
                    print("Message Id: 0x%x" %tx_msg.frame_id)
                    print("Data Length: %d" %tx_msg.length)

                    #get tx messages
                    rcv_can_list, rcv_canfd_list = get_msgs(all_can_list, all_canfd_list, tx_msg, TEST_NUM)

                    if len(rcv_can_list)+len(rcv_canfd_list) < TEST_NUM:
                        fail_cnt += 1
                        print("Get Frame error")
                        print("DLC Test Fail\n")
                        continue

                    for rcv_msg in rcv_can_list:
                        tx_msg_dlc_list.append(rcv_msg.frame.can_dlc)
                    for rcv_msg in rcv_canfd_list:
                        tx_msg_dlc_list.append(rcv_msg.frame.len)

                    for dlc in tx_msg_dlc_list:
                        if dlc != tx_msg.length:
                            err_cnt+=1
                            print("DLC Err Value:",dlc)

                    print("Number Of Frame:",len(tx_msg_dlc_list))
                    print("DLC Max:",max(tx_msg_dlc_list))
                    print("DLC Min:",min(tx_msg_dlc_list))
                    
                    if err_cnt > 0:
                        print("DLC Err Cnt:",err_cnt)
                        fail_cnt += 1
                        print("DLC Test Fail\n")
                    else:
                        pass_cnt += 1
                        print("DLC Test Pass\n")
        print("Total Message:",test_cnt)
        print("Pass:",pass_cnt)
        print("Fail:",fail_cnt)
        print("NA:",test_cnt-pass_cnt-fail_cnt)
        if fail_cnt > 0:
            self.fail_cnt += 1
            print("CANTx DLC Test Fail")
        else:
            self.pass_cnt += 1
            print("CANTx DLC Test Pass")
        print("CANTx DLC Test Done")

    def period_check(self, dbc_analyzer_obj, all_can_list, all_canfd_list):
        self.test_cnt += 1
        print('\n****** TC %d ******'%self.test_cnt)
        print("CANTx Period Test Start...")
        test_cnt = 0
        pass_cnt = 0
        fail_cnt = 0
        for channel_obj in dbc_analyzer_obj.channel_obj_list:
            print("Channel_Name:",channel_obj.channel_name)
            for tx_msg in channel_obj.tx_msg_list:
                if tx_msg.send_type == 'Cyclic':
                    period_list = []# ms
                    period_time_last = 0
                    period_tolerance = 0
                    period_avg_err = 0
                    period_sum = 0
                    period_avg = 0
                    err_cnt = 0
                    test_cnt += 1
                    print("Message Name: %s" %tx_msg.name,)
                    print("Message Id: 0x%x" %tx_msg.frame_id)
                    print("Cycle Time: %dms" %tx_msg.cycle_time)

                    msg_cycle_time = tx_msg.cycle_time
                    if msg_cycle_time > 500:
                        period_tolerance = 50
                    elif msg_cycle_time > 100:
                        period_tolerance = msg_cycle_time/10
                    elif msg_cycle_time >= 20:
                        period_tolerance = 10
                    else:
                        period_tolerance = msg_cycle_time/2

                    #get tx messages
                    rcv_can_list, rcv_canfd_list = get_msgs(all_can_list, all_canfd_list, tx_msg, TEST_NUM+1)

                    if len(rcv_can_list)+len(rcv_canfd_list) < TEST_NUM+1:
                        fail_cnt += 1
                        print("Get Frame error")
                        print("Period Test Fail\n")
                        continue

                    for rcv_msg in rcv_can_list+rcv_canfd_list:
                        if period_time_last == 0:
                            period_time_last = rcv_msg.timestamp/1000
                        else:
                            period_list.append(round(rcv_msg.timestamp/1000-period_time_last,2))
                            period_time_last = rcv_msg.timestamp/1000

                    for period in period_list:
                        period_sum += period
                        if abs(period-msg_cycle_time) > period_tolerance:
                            err_cnt+=1
                            print("Period Err Value:",period)
                    period_avg = round(period_sum/TEST_NUM,2)
                    if abs(period_avg-msg_cycle_time) > msg_cycle_time/50:
                        period_avg_err = 1
                    print("Number Of Frame:",len(period_list))
                    print("Period Max:",max(period_list))
                    print("Period Min:",min(period_list))
                    print("Period Avg:",period_avg)
                    if period_avg_err > 0:
                        print("Average Period Out Of Range:")
                    if err_cnt > 0:
                        print("Period Err Cnt:",err_cnt)
                    
                    if period_avg_err == 0 and err_cnt == 0:
                        pass_cnt += 1
                        print("Period Test Pass\n")
                    else:
                        fail_cnt += 1
                        print("Period Test Fail\n")
        print("Total Message:",test_cnt)
        print("Pass:",pass_cnt)
        print("Fail:",fail_cnt)
        print("NA:",test_cnt-pass_cnt-fail_cnt)
        if fail_cnt > 0:
            self.fail_cnt += 1
            print("CANTx Period Test Fail")
        else:
            self.pass_cnt += 1
            print("CANTx Period Test Pass")
        print("CANTx Period Test Done")

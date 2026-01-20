# -*- coding:utf-8 -*-
from ctypes import *
import platform
import threading

import time

ZCAN_DEVICE_TYPE = c_uint

INVALID_DEVICE_HANDLE  = 0
INVALID_CHANNEL_HANDLE = 0

# Device Type
ZCAN_USBCANFD_200U    = ZCAN_DEVICE_TYPE(41)

# Interface return status
ZCAN_STATUS_ERR         = 0
ZCAN_STATUS_OK          = 1
ZCAN_STATUS_ONLINE      = 2
ZCAN_STATUS_OFFLINE     = 3
ZCAN_STATUS_UNSUPPORTED = 4

# CAN type
ZCAN_TYPE_CAN    = c_uint(0)
ZCAN_TYPE_CANFD  = c_uint(1)

def input_thread():
   input()

# Device information
class ZCAN_DEVICE_INFO(Structure):
    _fields_ = [("hw_Version", c_ushort),
                ("fw_Version", c_ushort),
                ("dr_Version", c_ushort), 
                ("in_Version", c_ushort), 
                ("irq_Num", c_ushort),
                ("can_Num", c_ubyte),
                ("str_Serial_Num", c_ubyte * 20),
                ("str_hw_Type", c_ubyte * 40),
                ("reserved", c_ushort * 4)]

    def __str__(self):
        return "Hardware Version:%s\nFirmware Version:%s\nDriver Interface:%s\nInterface Interface:%s\nInterrupt Number:%d\nCAN Number:%d\nSerial:%s\nHardware Type:%s\n" %(
                self.hw_version, self.fw_version, self.dr_version, self.in_version, self.irq_num, self.can_num, self.serial, self.hw_type)
                
    def _version(self, version):
        return ("V%02x.%02x" if version // 0xFF >= 9 else "V%d.%02x") % (version // 0xFF, version & 0xFF)
    
    @property
    def hw_version(self):
        return self._version(self.hw_Version)

    @property
    def fw_version(self):
        return self._version(self.fw_Version)
    
    @property
    def dr_version(self):
        return self._version(self.dr_Version)
    
    @property
    def in_version(self):
        return self._version(self.in_Version)

    @property
    def irq_num(self):
        return self.irq_Num

    @property
    def can_num(self):
        return self.can_Num

    @property
    def serial(self):
        serial = ''
        for c in self.str_Serial_Num:
            if c > 0: 
               serial += chr(c)
            else:
                break 
        return serial

    @property
    def hw_type(self):
        hw_type = ''
        for c in self.str_hw_Type:
            if c > 0:
                hw_type += chr(c)
            else:
                break
        return hw_type

class _ZCAN_CHANNEL_CAN_INIT_CONFIG(Structure):
    _fields_ = [("acc_code", c_uint),
                ("acc_mask", c_uint),
                ("reserved", c_uint),
                ("filter",   c_ubyte),
                ("timing0",  c_ubyte),
                ("timing1",  c_ubyte),
                ("mode",     c_ubyte)]

class _ZCAN_CHANNEL_CANFD_INIT_CONFIG(Structure):
    _fields_ = [("acc_code",     c_uint),
                ("acc_mask",     c_uint),
                ("abit_timing",  c_uint),
                ("dbit_timing",  c_uint),
                ("brp",          c_uint),
                ("filter",       c_ubyte),
                ("mode",         c_ubyte),
                ("pad",          c_ushort),
                ("reserved",     c_uint)]

class _ZCAN_CHANNEL_INIT_CONFIG(Union):
    _fields_ = [("can", _ZCAN_CHANNEL_CAN_INIT_CONFIG), ("canfd", _ZCAN_CHANNEL_CANFD_INIT_CONFIG)]

class ZCAN_CHANNEL_INIT_CONFIG(Structure):
    _fields_ = [("can_type", c_uint),
                ("config", _ZCAN_CHANNEL_INIT_CONFIG)]

class ZCAN_CHANNEL_ERR_INFO(Structure):
    _fields_ = [("error_code", c_uint),
                ("passive_ErrData", c_ubyte * 3),
                ("arLost_ErrData", c_ubyte)]

class ZCAN_CHANNEL_STATUS(Structure):
    _fields_ = [("errInterrupt", c_ubyte),
                ("regMode",      c_ubyte),
                ("regStatus",    c_ubyte), 
                ("regALCapture", c_ubyte),
                ("regECCapture", c_ubyte),
                ("regEWLimit",   c_ubyte),
                ("regRECounter", c_ubyte),
                ("regTECounter", c_ubyte),
                ("Reserved",     c_ubyte)]

class ZCAN_CAN_FRAME(Structure):
    _fields_ = [("can_id",  c_uint, 29),
                ("err",     c_uint, 1),
                ("rtr",     c_uint, 1),
                ("eff",     c_uint, 1), 
                ("can_dlc", c_ubyte),
                ("__pad",   c_ubyte),
                ("__res0",  c_ubyte),
                ("__res1",  c_ubyte),
                ("data",    c_ubyte * 8)]

class ZCAN_CANFD_FRAME(Structure):
    _fields_ = [("can_id", c_uint, 29), 
                ("err",    c_uint, 1),
                ("rtr",    c_uint, 1),
                ("eff",    c_uint, 1), 
                ("len",    c_ubyte),
                ("brs",    c_ubyte, 1),
                ("esi",    c_ubyte, 1),
                ("__pad",  c_ubyte, 6),
                ("__res0", c_ubyte),
                ("__res1", c_ubyte),
                ("data",   c_ubyte * 64)]

class ZCANdataFlag(Structure):
    _pack_  =  1
    _fields_= [("frameType",c_uint,2),
               ("txDelay",c_uint,2),
               ("transmitType",c_uint,4),
               ("txEchoRequest",c_uint,1),
               ("txEchoed",c_uint,1),
               ("reserved",c_uint,22),
               ]

class ZCANFDData(Structure):            ##表示 CAN/CANFD 帧结构,目前仅作为 ZCANDataObj 结构的成员使用
    _pack_  =  1
    _fields_= [("timestamp",c_uint64),
               ("flag",ZCANdataFlag),
               ("extraData",c_ubyte*4),
               ("frame",ZCAN_CANFD_FRAME),]

class ZCANDataObj(Structure):
    _pack_  =  1
    _fields_= [("dataType",c_ubyte),
               ("chnl",c_ubyte),
               ("flag",c_ushort),
               ("extraData",c_ubyte*4),
               ("zcanfddata",ZCANFDData),##88个字节
               ("reserved",c_ubyte*4),
               ]
    
class ZCAN_Transmit_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("transmit_type", c_uint)]

class ZCAN_Receive_Data(Structure):
    _fields_  = [("frame", ZCAN_CAN_FRAME), ("timestamp", c_ulonglong)]

class ZCAN_TransmitFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("transmit_type", c_uint)]

class ZCAN_ReceiveFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("timestamp", c_ulonglong)]

class ZCAN_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [("enable",   c_ushort),
                ("index",    c_ushort),
                ("interval", c_uint),
                ("obj",      ZCAN_Transmit_Data)]

class ZCANFD_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [("enable",   c_ushort),
                ("index",    c_ushort),
                ("interval", c_uint),
                ("obj",      ZCAN_TransmitFD_Data)]

class ZCANFD_AUTO_TRANSMIT_OBJ_PARAM(Structure):   #auto_send delay
    _fields_ = [("indix",  c_ushort),
                ("type",   c_ushort),
                ("value",  c_uint)]

class IProperty(Structure):
    _fields_ = [("SetValue", c_void_p), 
                ("GetValue", c_void_p),
                ("GetPropertys", c_void_p)]

class ZCAN(object):
    def __init__(self):
        if platform.system() == "Windows":
            self.__dll = windll.LoadLibrary("./zlgcan.dll")
        else:
            print("No support now!")
        if self.__dll == None:
            print("DLL couldn't be loaded!")

    def OpenDevice(self, device_type, device_index, reserved):
        try:
            return self.__dll.ZCAN_OpenDevice(device_type, device_index, reserved)
        except:
            print("Exception on OpenDevice!") 
            raise

    def CloseDevice(self, device_handle):
        try:
            return self.__dll.ZCAN_CloseDevice(device_handle)
        except:
            print("Exception on CloseDevice!")
            raise

    def GetDeviceInf(self, device_handle):
        try:
            info = ZCAN_DEVICE_INFO()
            ret = self.__dll.ZCAN_GetDeviceInf(device_handle, byref(info))
            return info if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_GetDeviceInf")
            raise

    def DeviceOnLine(self, device_handle):
        try:
            return self.__dll.ZCAN_IsDeviceOnLine(device_handle)
        except:
            print("Exception on ZCAN_ZCAN_IsDeviceOnLine!")
            raise

    def InitCAN(self, device_handle, can_index, init_config):
        try:
            return self.__dll.ZCAN_InitCAN(device_handle, can_index, byref(init_config))
        except:
            print("Exception on ZCAN_InitCAN!")
            raise

    def StartCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_StartCAN(chn_handle)
        except:
            print("Exception on ZCAN_StartCAN!")
            raise

    def ResetCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_ResetCAN(chn_handle)
        except:
            print("Exception on ZCAN_ResetCAN!")
            raise

    def ClearBuffer(self, chn_handle):
        try:
            return self.__dll.ZCAN_ClearBuffer(chn_handle)
        except:
            print("Exception on ZCAN_ClearBuffer!")
            raise

    def ReadChannelErrInfo(self, chn_handle):
        try:
            ErrInfo = ZCAN_CHANNEL_ERR_INFO()
            ret = self.__dll.ZCAN_ReadChannelErrInfo(chn_handle, byref(ErrInfo))
            return ErrInfo if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelErrInfo!")
            raise

    def ReadChannelStatus(self, chn_handle):
        try:
            status = ZCAN_CHANNEL_STATUS()
            ret = self.__dll.ZCAN_ReadChannelStatus(chn_handle, byref(status))
            return status if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelStatus!")
            raise

    def GetReceiveNum(self, chn_handle, can_type = ZCAN_TYPE_CAN):
        try:
            return self.__dll.ZCAN_GetReceiveNum(chn_handle, can_type)
        except:
            print("Exception on ZCAN_GetReceiveNum!")
            raise

    def Transmit(self, chn_handle, std_msg, len):
        try:
            return self.__dll.ZCAN_Transmit(chn_handle, byref(std_msg), len)
        except:
            print("Exception on ZCAN_Transmit!")
            raise

    def Receive(self, chn_handle, rcv_num, wait_time = c_int(-1)):
        try:
            rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
            ret = self.__dll.ZCAN_Receive(chn_handle, byref(rcv_can_msgs), rcv_num, wait_time)
            return rcv_can_msgs, ret
        except:
            print("Exception on ZCAN_Receive!")
            raise
    
    def TransmitFD(self, chn_handle, fd_msg, len):
        try:
            return self.__dll.ZCAN_TransmitFD(chn_handle, byref(fd_msg), len)
        except:
            print("Exception on ZCAN_TransmitFD!")
            raise
    
            
    def TransmitData(self,device_handle,msg,len):
        try:
            return self.__dll.ZCAN_TransmitData(device_handle,byref(msg),len)
        except:
            print("Exception on ZCAN_TransmitData!")
            raise
    def ReceiveFD(self, chn_handle, rcv_num, wait_time = c_int(-1)):
        try:
            rcv_canfd_msgs = (ZCAN_ReceiveFD_Data * rcv_num)()
            ret = self.__dll.ZCAN_ReceiveFD(chn_handle, byref(rcv_canfd_msgs), rcv_num, wait_time)
            return rcv_canfd_msgs, ret
        except:
            print("Exception on ZCAN_ReceiveF D!")
            raise

    def ReceiveData(self,device_handle,rcv_num,wait_time = c_int(-1)):
        try:
            rcv_can_data_msgs = (ZCANDataObj * rcv_num)()
            ret = self.__dll.ZCAN_ReceiveData(device_handle , rcv_can_data_msgs, rcv_num,wait_time)
            return  rcv_can_data_msgs ,ret
        except:
            print("Exception on ZCAN_ReceiveData!")
            raise


    def GetIProperty(self, device_handle):
        try:
            self.__dll.GetIProperty.restype = POINTER(IProperty)
            return self.__dll.GetIProperty(device_handle)
        except:
            print("Exception on ZCAN_GetIProperty!")
            raise

    def SetValue(self, iproperty, path, value):
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_char_p(value.encode("utf-8")))
        except:
            print("Exception on IProperty SetValue")
            raise
            
    def SetValue1(self, iproperty, path, value):                                              #############################
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_void_p(value))
        except:
            print("Exception on IProperty SetValue")
            raise
            

    def GetValue(self, iproperty, path):
        try:
            func = CFUNCTYPE(c_char_p, c_char_p)(iproperty.contents.GetValue)
            return func(c_char_p(path.encode("utf-8")))
        except:
            print("Exception on IProperty GetValue")
            raise

    def ReleaseIProperty(self, iproperty):
        try:
            return self.__dll.ReleaseIProperty(iproperty)
        except:
            print("Exception on ZCAN_ReleaseIProperty!")
            raise
        
    def ZCAN_SetValue(self,device_handle,path,value):
        try:
            self.__dll.ZCAN_SetValue.argtypes=[c_void_p,c_char_p,c_void_p]
            return self.__dll.ZCAN_SetValue(device_handle,path.encode("utf-8"),value)
        except:
            print("Exception on ZCAN_SetValue")
            raise
    
    def ZCAN_GetValue(self,device_handle,path):
        try:
            self.__dll.ZCAN_GetValue.argtypes =[c_void_p,c_char_p]
            self.__dll.ZCAN_GetValue.restype =c_void_p
            return self.__dll.ZCAN_GetValue(device_handle,path.encode("utf-8"))
        except:
            print("Exception on ZCAN_GetValue")
            raise
            
class Zlgcan:
    def canfd_start(zcanlib, device_handle, chn):
        ret = zcanlib.ZCAN_SetValue(device_handle, str(chn) + "/canfd_standard", "0".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d CANFD standard failed!" %(chn))
        ret = zcanlib.ZCAN_SetValue(device_handle, str(chn) + "/initenal_resistance", "1".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Open CH%d resistance failed!" %(chn))
            exit(0)

        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/canfd_abit_baud_rate","500000".encode("utf-8"))  #设置波特率
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/canfd_dbit_baud_rate","2000000".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d baud failed!" %(chn))      
            exit(0)
            
        ret = zcanlib.ZCAN_SetValue(device_handle, "0/set_cn","A001".encode("utf-8"))
        if ret == ZCAN_STATUS_OK:
            t = zcanlib.ZCAN_GetValue(device_handle, "0/get_cn/1")
            # print(c_char_p(t).value.decode("utf-8"))

        chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = ZCAN_TYPE_CANFD
        chn_init_cfg.config.canfd.mode  = 0
        chn_handle = zcanlib.InitCAN(device_handle, chn, chn_init_cfg)
        if chn_handle ==0:
            print("initCAN failed!" %(chn))  
            exit(0)
    ###SET filter  
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_clear","0".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_clear failed!" %(chn))
            exit(0)
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_mode","0".encode("utf-8"))    #标准帧滤波
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_mode failed!" %(chn)) 
            exit(0)
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_start","0".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_start failed!" %(chn))  
            exit(0)        
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_end","0x7FF".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_end failed!" %(chn)) 
            exit(0)
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_mode","1".encode("utf-8"))    #扩展帧滤波
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_mode failed!" %(chn))
            exit(0)
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_start","0".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_start failed!" %(chn))
            exit(0)        
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_end","0x1FFFFFFF".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_end failed!" %(chn))
            exit(0)
        ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/filter_ack","0".encode("utf-8"))
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d  filter_ack failed!" %(chn))
            exit(0)

        ret=zcanlib.StartCAN(chn_handle)
        if ret != ZCAN_STATUS_OK:
            print("startCAN failed!" %(chn))
            exit(0)  

        # ret = zcanlib.ZCAN_SetValue(device_handle,str(chn)+"/set_device_tx_echo","1".encode("utf-8"))   #发送回显设置，0-禁用，1-开启
        # if ret != ZCAN_STATUS_OK:
        #     print("Set CH%d  set_device_tx_echo failed!" %(chn))
        #     exit(0)

        return chn_handle

    def Message_Send(zcanlib,chn_handle):
        #Send CAN Messages
        # transmit_num = 10
        # msgs = (ZCAN_Transmit_Data * transmit_num)()
        # for i in range(transmit_num):
        #     msgs[i].transmit_type = 0 #0-正常发送，2-自发自收
        #     msgs[i].frame.eff     = 0 #0-标准帧，1-扩展帧
        #     msgs[i].frame.rtr     = 0 #0-数据帧，1-远程帧
        #     msgs[i].frame.can_id  = i
        #     msgs[i].frame.can_dlc = 8
        #     for j in range(msgs[i].frame.can_dlc):
        #         msgs[i].frame.data[j] = j
        # ret = zcanlib.Transmit(chn_handle, msgs, transmit_num)
        # print("Tranmit Num: %d." % ret)
        
        #Send CANFD Messages
        transmit_canfd_num = 10
        canfd_msgs = (ZCAN_TransmitFD_Data * transmit_canfd_num)()
        for i in range(transmit_canfd_num):
            canfd_msgs[i].transmit_type = 0 #0-正常发送，2-自发自收
            canfd_msgs[i].frame.eff     = 0 #0-标准帧，1-扩展帧
            canfd_msgs[i].frame.rtr     = 0 #0-数据帧，1-远程帧
            canfd_msgs[i].frame.brs     = 1 #BRS 加速标志位：0不加速，1加速
            canfd_msgs[i].frame.can_id  = i+0x100
            canfd_msgs[i].frame.len     = 8
            for j in range(canfd_msgs[i].frame.len):
                canfd_msgs[i].frame.data[j] = i
                
            ret = zcanlib.TransmitFD(chn_handle, canfd_msgs[i], 1)
            # print("Tranmit CANFD Num: %d." % i)
            time.sleep(1)

    def Message_Receive(zcanlib,chn_handle):
        #Receive Messages
        rcv_canfd_msgs = []
        rcv_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CAN)
        rcv_canfd_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CANFD)
        if rcv_num:
            rcv_msg, rcv_num = zcanlib.Receive(chn_handle, rcv_num)
        #     for i in range(rcv_num):
        #         print("timestamps:%6fs,type:CAN, %s ,id:%s, dlc:%d, eff:%d, rtr:%d, data:%s" %(
        #         rcv_msg[i].timestamp/1000000,"tx" if (rcv_msg[i].frame.__pad&0x20) else "rx",
        #         hex(rcv_msg[i].frame.can_id), rcv_msg[i].frame.can_dlc,
        #         rcv_msg[i].frame.eff, rcv_msg[i].frame.rtr,
        #         ''.join(hex(rcv_msg[i].frame.data[j])+ ' 'for j in range(rcv_msg[i].frame.can_dlc))))
        if rcv_canfd_num:
            rcv_canfd_msgs, rcv_canfd_num = zcanlib.ReceiveFD(chn_handle, rcv_canfd_num)
            # for i in range(rcv_canfd_num):
            #     print("timestamp:%6fs,type:canfd, %s ,id:%s, len:%d, eff:%d, rtr:%d, esi:%d, brs: %d, data:%s" %(
            #     rcv_canfd_msgs[i].timestamp/1000000,"tx" if (rcv_canfd_msgs[i].frame.__pad&0x8) else "rx" ,
            #     hex(rcv_canfd_msgs[i].frame.can_id), rcv_canfd_msgs[i].frame.len,
            #     rcv_canfd_msgs[i].frame.eff, rcv_canfd_msgs[i].frame.rtr,
            #     rcv_canfd_msgs[i].frame.esi, rcv_canfd_msgs[i].frame.brs,
            #     ''.join(hex(rcv_canfd_msgs[i].frame.data[j]) + ' ' for j in range(rcv_canfd_msgs[i].frame.len))))
        return rcv_canfd_msgs

    def Open_Device(zcanlib):
        testcantype =1 #0:CAN; 1:canfd
        handle = zcanlib.OpenDevice(ZCAN_USBCANFD_200U, 0, 0)
        if handle == INVALID_DEVICE_HANDLE:
            print("Open CANFD Device failed!")
            exit(0)
        print("device handle:%d" %(handle))

        return handle

    # threads=[]

    # thread=threading.Thread(target=Message_Send, args=(chn0_handle,))
    # thread.start()
    # threads.append(thread)
    # thread1=threading.Thread(target=input_thread)
    # thread1.start()
    # Message_Receive(chn1_handle)
    # threads.append(thread1)

    # for thread in threads:
    #     thread.join()


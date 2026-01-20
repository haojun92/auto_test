from ctypes import *
from lib.zlgcan import *
from lib.zuds_structure import *
import platform
import threading
import time
import datetime


class PARAM_DATA(Structure):    #用于存放uds的参数内容
    _pack_=1
    _fields_=[("data",c_ubyte*4096)]

class CHANNEL_PARAM(Structure):
    _fields_=[("channel_handle",c_uint32),      #通道句柄
              ("Extend_Flag",c_uint32),         #0-standard_frame, 1-extern_frame
              ("CANFD_type",c_uint32),          #0-can,1-canfd
              ("trans_version",c_uint32),       #0-ISO15765-2004,1-ISO15765-2016
              ]


@WINFUNCTYPE(c_uint32, POINTER(CHANNEL_PARAM), POINTER(ZUDS_FRAME), c_uint32)   #设置发送回调实例
def transmit_callback(ctx, frame, count):
    #print("frame num is:%d"%count)
    if  ctx.contents.CANFD_type:
        zcanfd_data=(ZCAN_TransmitFD_Data*count)()
        memset(zcanfd_data,0,sizeof(zcanfd_data))
        for i in range(count):
            zcanfd_data[i].frame.can_id = frame[i].id
            if ctx.contents.Extend_Flag:
                zcanfd_data[i].frame.eff = 1
            zcanfd_data[i].frame.len = frame[i].data_len  # frame[i].data_len
            zcanfd_data[i].frame.__pad =0x08  #设置发送回显
            for j in range(frame[i].data_len):
                zcanfd_data[i].frame.data[j] = frame[i].data[j]
        result = zcanlib.TransmitFD(ctx.contents.channel_handle, zcanfd_data, count)
    else:
        zcan_data = (ZCAN_Transmit_Data * count)()
        memset(zcan_data,0,sizeof(zcan_data))#确保队列发送中的“帧间隔为0”
        for i in range(count):
            zcan_data[i].frame.can_id = frame[i].id
            if ctx.contents.Extend_Flag:
                zcan_data[i].frame.eff=1
            zcan_data[i].frame.can_dlc = frame[i].data_len   #frame[i].data_len
            #zcan_data[i].frame.__pad =0x20  #设置发送回显
            for j in range(frame[i].data_len):
                zcan_data[i].frame.data[j] = frame[i].data[j]
        result = zcanlib.Transmit(ctx.contents.channel_handle, zcan_data, count)
    if result ==count:
        return 0
    else:
        return 1


class ZUDS(object):
    def __init__(self):
        if platform.system() == "Windows":
            self.__dll = windll.LoadLibrary("./lib/zuds.dll")
        else:
            print("No support now!")
        if self.__dll == None:
            print("DLL couldn't be loaded!")

    def Uds_Init(self,type_):
        try:
            return self.__dll.ZUDS_Init(type_)
        except:
            print("Excetion on Udsinit")

    def Uds_SetTransmitHandler(self,zuds_handle,ctx):
        try:
            return self.__dll.ZUDS_SetTransmitHandler(zuds_handle,ctx, transmit_callback)
        except:
            print("Exception on SetTransmitHandler")

    def Uds_Request(self, handle, request, response):
        try:
            return self.__dll.ZUDS_Request(handle, byref(request),byref(response))
        except:
            print("Exception on UDSRequest")
            
    def Uds_Onreceive(self, handle, uds_frame):
        try:
            return self.__dll.ZUDS_OnReceive(handle, byref(uds_frame))
        except:
            print("Exception on uds_Onreceive")
            
    def Uds_SetParam(self, handle, type_, param): #type =0设置ZUDS_SESSION_PARAM，type=1设置ZUDS_ISO15765_PARAM
        try:
            return self.__dll.ZUDS_SetParam(handle, type_, byref(param))
        except:
            print("Exception on uds_SetParam")

    def Uds_SetTesterPresent(self , handle, enable, param ):
        try:
            return self._dll.ZUDS_SetTesterPresent(handle, enable, byref(param))
        except:
            print("Exception on SetTesterPresent")

    def Uds_Release(self, handle):
        try:
            return self.__dll.ZUDS_Release(handle)
        except:
            print("Exception on uds_Release")

    def Uds_Stop(self,handle):
        try:
            return self.__dll.ZUDS_Stop(handle)
        except:
            print("Exception on UDS_STOP")

def Set_param(uds_handle,chn_param):
    param_15765 =ZUDS_ISO15765_PARAM()
    memset(byref(param_15765),0,sizeof(param_15765))
    param_15765.version =chn_param.trans_version  #
    param_15765.max_data_len = 64 if chn_param.trans_version else 8
    param_15765.local_st_min = 0
    param_15765.block_size   = 8
    param_15765.fill_byte    = 0
    param_15765.frame_type   = chn_param.Extend_Flag #0-标准帧，1-扩展帧
    param_15765.is_modify_ecu_st_min =0 # 是否修改 ECU 的最小发送时间间隔参数
    param_15765.remote_st_min = 0
    param_15765.fc_timeout    = 70  #等待流控超时时间，单位ms
    param_15765.fill_mode     = 1   #数据长度填充模式，0-不填充，1-小于8字节填充到8，大于8字节就近填充，2-填充至最大字节
    zudslib.Uds_SetParam(uds_handle, 1, param_15765)   #第二个参数为1对应15765结构体
    
    param_seesion =ZUDS_SESSION_PARAM()
    memset(byref(param_seesion),0,sizeof(param_seesion))
    param_seesion.timeout =2000
    param_seesion.enhanced_timeout =5000
    zudslib.Uds_SetParam(uds_handle, 0 ,param_seesion)  #第二个参数为0对应 应用层结构体
    # print("set_param completed")

def Read_Thread_Func(chn_handle,uds_handle):        #独立的循环接收线程，把接收数据丢给UDS库处理。
    uds_frame = ZUDS_FRAME()
    while start_receive_flag:
        
        rcv_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CAN)
        rcv_canfd_num = zcanlib.GetReceiveNum(chn_handle,ZCAN_TYPE_CANFD)
        if rcv_num:
            rcv_msg, rcv_num = zcanlib.Receive(chn_handle, rcv_num,1)
            for i in range(rcv_num):
                memset(byref(uds_frame),0,sizeof(uds_frame))
                uds_frame.id        =rcv_msg[i].frame.can_id&0x1fffffff #传入真实ID
                uds_frame.extend    =rcv_msg[i].frame.eff
                uds_frame.data_len  =rcv_msg[i].frame.can_dlc
                for j in range(uds_frame.data_len):
                    uds_frame.data[j]=rcv_msg[i].frame.data[j]
                # print("[%d]:timestamps:%d,type:CAN, %s ,id:%s, dlc:%d, eff:%d, rtr:%d, data:%s" %(i,
                #       rcv_msg[i].timestamp,"tx" if (rcv_msg[i].frame.__pad&0x20) else "rx",
                #       hex(rcv_msg[i].frame.can_id), rcv_msg[i].frame.can_dlc,
                #       rcv_msg[i].frame.eff, rcv_msg[i].frame.rtr,
                #       ''.join(hex(rcv_msg[i].frame.data[j])+ ' 'for j in range(rcv_msg[i].frame.can_dlc))))
                zudslib.Uds_Onreceive(uds_handle,uds_frame)
        if rcv_canfd_num:
            rcv_canfd_msgs, rcv_canfd_num = zcanlib.ReceiveFD(chn_handle, rcv_canfd_num, 1)
            for i in range(rcv_canfd_num):
                memset(byref(uds_frame),0,sizeof(uds_frame))
                uds_frame.id        =rcv_canfd_msgs[i].frame.can_id&0x1fffffff #传入真实ID
                uds_frame.extend    =rcv_canfd_msgs[i].frame.eff
                uds_frame.data_len  =rcv_canfd_msgs[i].frame.len
                for j in range(uds_frame.data_len):
                    uds_frame.data[j]   =rcv_canfd_msgs[i].frame.data[j]
                # print("[%d]:timestamp:%d,type:canfd, %s ,id:%s, len:%d, eff:%d, rtr:%d, esi:%d, brs: %d, data:%s" %(
                #         i, rcv_canfd_msgs[i].timestamp,"tx" if (rcv_canfd_msgs[i].frame.__pad&0x8) else "rx" ,
                #         hex(rcv_canfd_msgs[i].frame.can_id), rcv_canfd_msgs[i].frame.len,
                #         rcv_canfd_msgs[i].frame.eff, rcv_canfd_msgs[i].frame.rtr,
                #         rcv_canfd_msgs[i].frame.esi, rcv_canfd_msgs[i].frame.brs,
                #         ''.join(hex(rcv_canfd_msgs[i].frame.data[j]) + ' ' for j in range(rcv_canfd_msgs[i].frame.len))))
                zudslib.Uds_Onreceive(uds_handle,uds_frame)
        time.sleep(0.01)
    # print("exit receive")
  
def uds_req(t_zcanlib,chn_handle,data,project):
    global zcanlib
    zcanlib = t_zcanlib
    global zudslib
    zudslib = ZUDS()
     
    global start_receive_flag
    start_receive_flag = 0
    #UDS初始化
    uds_handle= zudslib.Uds_Init(0)                           #初始化UDS，获取UDS句柄
    # print("uds_handle is %d"%uds_handle)

    chn_param=CHANNEL_PARAM()
    chn_param.channel_handle=chn_handle
    chn_param.Extend_Flag =0                #0-标准帧，1-扩展帧
    chn_param.CANFD_type=1                  #0-CAN,1-CANFD
    chn_param.trans_version=0               #0-2004版本，1-2016版本
    ret =zudslib.Uds_SetTransmitHandler(uds_handle,byref(chn_param))#设置发送回调,将uds句柄与通道句柄绑定
    if ret==0:
        # print("Uds_SetTransmitHandler success")
        pass
    else:
        print("Uds_SetTransmitHandler fail")
        exit(0)

    Set_param(uds_handle,chn_param)
    
    start_receive_flag=1   
    read_thread_ = threading.Thread(None,target = Read_Thread_Func,args=(chn_handle,uds_handle))
    read_thread_.start()
    
    # print("request ")  
    request= ZUDS_REQUEST()   
    memset(byref(request),0,sizeof(request))

    if project == "E01":
        request.src_addr=0x742
        request.dst_addr=0x7C2
    else:
        request.src_addr=0x7C0
        request.dst_addr=0x7D0
        
    request.sid = data[0]
    request.suppress_response =0 #抑制响应标志位 ，0-不开启抑制，库会等响应  1-抑制响应，库不等ECU回复
    request.param_len=len(data)-1      #参数长度
    param_data=PARAM_DATA()  #参数的list，成员数量需与request.param_len对应     
    for i in range(request.param_len):
        param_data.data[i]=data[i+1]
    request.param =param_data.data
    response =ZUDS_RESPONSE()

    zudslib.Uds_Request(uds_handle,request,response)
    print("UDS Request: %s %s %s"%(hex(request.param_len+1),hex(request.sid),''.join(hex(request.param[i])+' 'for i in range(request.param_len))))
    memset(byref(param_data),0,sizeof(param_data))
    if response.status==0:
        if response.type ==0:
            print("Negative Response:%s %s %s"%(hex(response.response.negative.neg_code),hex(response.response.negative.sid),hex(response.response.negative.error_code))) 
            # print("消极响应：%s, 服务号：%s, 消极码：%s"%(hex(response.response.negative.neg_code),hex(response.response.negative.sid),hex(response.response.negative.error_code)))
        if response.type ==1:
            print("Positive Response:%s %s"%(hex(response.response.positive.sid),''.join(hex(response.response.positive.param[i])+' 'for i in range(response.response.positive.param_len))))
            # print("积极响应\n响应id:%s, 参数长度:%d, 参数内容：%s"%(hex(response.response.positive.sid),response.response.positive.param_len,''.join(hex(response.response.positive.param[i])+' 'for i in range(response.response.positive.param_len))))
    if response.status ==1:
        print("响应超时")
    if response.status ==2:
        print("传输失败，请检查链路层，或请确认流控帧是否回复")
    if response.status ==3:
        print("取消请求")
    if response.status ==4:
        print("抑制响应")
    if response.status ==5:
        print("忙碌中")
    if response.status ==6:
        print("请求参数错误")
    
    time.sleep(2)
    start_receive_flag=0
    read_thread_.join()
    zudslib.Uds_Stop(uds_handle)
    
    return response
    
    

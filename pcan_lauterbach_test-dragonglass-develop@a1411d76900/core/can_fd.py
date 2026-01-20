"""
连接CAN FD
"""
import time
import binascii
from cantools import database
from pcan_ext.pcan import PCan
from pcan_ext.threads import Repeater
from PCANBasic import PCAN_USBBUS2, PCAN_USBBUS1
import cantools

class MyCanFD:
    def __init__(self, dbc: str):
        print("初始化...")
        self.ch = PCan(
            config={
                'handle': PCAN_USBBUS1,
                'baud_rate': b'f_clock=80000000, nom_brp=10, nom_tseg1=12, nom_tseg2=3, nom_sjw=1, data_brp=4, data_tseg1=7, data_tseg2=2, data_sjw=1',
            },
            dbc=dbc,
            fd=True,
            log=True,
            decode=True,
        )
        self.dbc = dbc
        self.db = cantools.db.load_file(self.dbc)
        print("初始化完成")

    def read(self, raw=False, thread_=False, time_gap=10):
        """
        读
        :param raw: raw数据标识
        :param thread_:
        :param time_gap: 时间间隔
        :return:
        """
        self.ch.log = True
        self.ch.decode = True if raw else False
        if thread_:
            r = Repeater(function=self.ch.read)
            r.start()
            time.sleep(time_gap)
            r.cancel()
        else:
            self.ch.read()

    # def write_raw(self, frame_id: int, data: str, thread_=False, time_gap=10):
    #     """
    #     写
    #     :param time_gap:
    #     :param thread_:
    #     :param frame_id: 如=0x500
    #     :param data: 发送的数据
    #     :return:
    #     """
    #     if not thread_:
    #         self.ch.write(frame_id=frame_id, data=binascii.unhexlify(data))
    #     else:
    #         w = Repeater(
    #             function=self.ch.write,
    #             kwargs=dict(
    #                 frame_id=frame_id,
    #                 data=binascii.unhexlify(data)
    #             )
    #         )
    #         w.start()
    #         time.sleep(time_gap)
    #         w.cancel()

    def write(self, msg, msg_name: str, thread_=False, time_gap=10):
        """
        普通写
        :param msg:
        :param msg_name:
        :param thread_:
        :param time_gap:
        :return:
        """
        print("开始写")
        _msg = self._write_init(msg=msg, msg_name=msg_name)
        if not thread_:
            self.ch.write(frame_id=_msg.frame_id)
        else:
            w = Repeater(
                function=self.ch.write,
                kwargs=dict(frame_id=_msg.frame_id, data=binascii),
                interval=_msg.cycle_time
            )
            w.start()
            time.sleep(time_gap)
            w.cancel()

    def _write_init(self, msg: dict, msg_name: str):
        message: database.Message = self.ch.db.get_message_by_name(msg_name)
        self.ch.bus.Tx[message.frame_id] = msg
        return message

    def read_and_write(self, write_msg: dict, msg_name: str, time_gap = 10):
        """
        同时读写
        :return:
        """
        _msg = self._write_init(msg=write_msg, msg_name=msg_name)

        w = Repeater(
            function=self.ch.write,
            kwargs=dict(frame_id=_msg.frame_id),
            interval=_msg.cycle_time
        )
        r = Repeater(function=self.ch.read, kwargs=dict(log=True, decode=True))

        w.start()
        r.start()

        time.sleep(time_gap)

        w.cancel()
        r.cancel()

    def load_dbc(self):
        # my_dbc = r"C:\001_work\QH01\DBC\CMX-V3.33(ADCC)&V3.22(FCM) For OT3\ADCC-V3.33\ADCC\BEV_E0X_OT_Car ADCC_FRM(HOLO) Message list  V3.33 Draft _202304111316_pcan.dbc"

        # print(db.messages)
        # 整理数据
        data = {}
        for m in self.db.messages:
            msg_name = m.name
            msg_dict = {}
            for i in m._signals:
                max_value = i.maximum
                min_value = i.minimum
                # msg_dict[i.name] = i.initial or 0
                msg_dict[i.name] = round((max_value+min_value/2))
            data[msg_name] = msg_dict
        return data

    def get_dbc_variables_info(self):
        """
        获取dbc变量数据信息
        :return:
        """
        result = {}
        # self.db.messages.__getattribute__("FLCR_Message")
        for m in self.db.messages:
            msg_name = m.name
            variable_dict = {}
            for i in m._signals:
                max_value = i.maximum
                min_value = i.minimum
                variable_name = i.name
                variable_dict[variable_name] = {"max": max_value, "min": min_value}
            result[msg_name] = variable_dict
        return result


if __name__ == '__main__':
    my_dbc = r"C:\001_work\QH01\lauterbach_test\test_4R4V\dbc\BEV_E0X_OT_Car ADCC_FLCR Message list  V3.33 Draft _202304111316_pcan.dbc"
    # my_dbc=None
    t = MyCanFD(my_dbc)

    # 读取dbc文件数据
    msg_dict = t.load_dbc()

    # 更新数据
    msg_dict["LCR_Header"].update({
        "LCR_Hdr_BlkSts": 1
    })
    t.write(
        msg=msg_dict["LCR_Header"],
        msg_name="LCR_Header"
    )
    print("*"*20)
    print(t.get_dbc_variables_info())
    print(123)


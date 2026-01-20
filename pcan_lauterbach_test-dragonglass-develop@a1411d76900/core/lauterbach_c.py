"""
lauterbach读写程序
"""
import time
from lauterbach.trace32.rcl import Debugger


class MyLauterbach:

    def __init__(self,
                 node="localhost",
                 port=20000,
                 packlen=1024,
                 protocol="TCP",
                 timeout=10.0
                 ):
        self.dbg = Debugger(node=node, port=port, packlen=packlen, protocol=protocol, timeout=timeout)

    def read(self, variable_full_name: str):
        """

        :param variable_full_name: 变量全名，如FLCR_Message.FLCR_Failure.FLCR_BlkSts
        :return:
        """
        value = self.dbg.variable.read(variable_full_name).value
        return value

    def __del__(self):
        self.dbg.disconnect()


if __name__ == '__main__':
    da_lao = MyLauterbach()
    v_f_name = "FLCR_Message.FLCR_Failure.FLCR_BlkSts"
    x = da_lao.read(v_f_name)
    print(x)


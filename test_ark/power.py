import serial


class Power(object):
    """
    程控电源接口 https://holomatic.feishu.cn/wiki/EG5jwckLPiBBJrkepd9cOCAqnee
    """

    def __init__(self, portx: str = "COM3", bps: int = 9600, timeout: float = 5.0) -> None:
        self._ser = serial.Serial(portx, bps, timeout=timeout)

    def read(self) -> str:
        output = b""
        while True:
            buffer = self._ser.read()
            if buffer == b"\n":
                break
            output += buffer
        return output.decode("utf-8")

    def write(self, command: str) -> None:
        self._ser.write(command.encode("utf-8"))
        self._ser.write(b"\n")

    def on(self):
        return self.write(":OUTP ON")

    def off(self):
        return self.write(":OUTP OFF")

    @property
    def v(self):
        self.write(":MEAS?")
        return self.read()

    @v.setter
    def v(self, value: float):
        self.write(f":VOLT {value}")

    @property
    def a(self):
        self.write(":MEAS:CURR?")
        return self.read()

    @a.setter
    def a(self, value: float):
        self.write(f":CURR {value}")

    @property
    def w(self):
        self.write(":MEAS:POW?")
        return self.read()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} v={self.v} a={self.a}>"

    __repr__ = __str__


if __name__ == "__main__":
    ...
    # import time
    #
    # power = Power()
    # print(power)
    # print(power.v, power.a, power.w)
    # power.off()
    # print(power.v, power.a, power.w)
    # time.sleep(5)
    # print(power.v, power.a, power.w)
    # power.on()
    # print(power.v, power.a, power.w)

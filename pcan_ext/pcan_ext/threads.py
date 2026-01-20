import threading

import win32event

from pcan_ext.logger import logger


class Thread(threading.Thread):
    def __init__(self, ch, args=None, kwargs=None) -> None:
        super().__init__()

        self.ch = ch  # TODO: typing

        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = threading.Event()

    def cancel(self):
        self.finished.set()


class RxThread(Thread):
    def run(self):
        event = win32event.CreateEvent(None, 0, 0, None)
        self.ch.set_receive_event(event.handle)
        try:
            while not self.finished.is_set():
                if win32event.WaitForSingleObject(event, 50) == win32event.WAIT_OBJECT_0:
                    self.ch.read_messages(*self.args, **self.kwargs)
        except KeyboardInterrupt:
            raise
        finally:
            self.ch.set_receive_event(0)


class TxThread(Thread):
    def __init__(self, ch, interval, args=None, kwargs=None) -> None:
        super().__init__(ch, args, kwargs)

        self.interval = interval

    def run(self):
        while not self.finished.is_set():
            self.finished.wait(self.interval / 1000)
            self.ch.write_message(*self.args, **self.kwargs)

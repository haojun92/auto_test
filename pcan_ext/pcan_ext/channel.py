import abc
import typing

from pcan_ext.callback import callback_rx, callback_tx
from pcan_ext.constant import SWAPPED_DLC_MAPPING
from pcan_ext.error import PCanError
from pcan_ext.logger import logger
from pcan_ext.threads import RxThread, TxThread
from PCANBasic import *  # noqa


class Channel(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        # 需要安装驱动 https://www.peak-system.com/Drivers.523.0.html?&L=1
        self.dll = PCANBasic()

        self.handle: TPCANHandle = None
        self._channel: TPCANChannelInformation = None
        self.fd: typing.Optional[bool] = False

    @property
    def info(self) -> TPCANChannelInformation:
        return self._channel

    @property
    def name(self) -> str:
        if self.handle.value < 0x100:
            channel_id = self.handle.value & 0xF
        else:
            channel_id = self.handle.value & 0xFF
        return f"{self.info.device_name.decode('utf-8')} {channel_id}".replace(" ", "_")

    def _request(self, f: typing.Callable, *args, **kwargs) -> typing.List[typing.Any]:
        result = f(*args, **kwargs)
        if isinstance(result, TPCANStatus):
            status, *result = result, None
        else:
            status, *result = result

        if status == PCAN_ERROR_OK:
            logger.info(f"{f.__name__} success")
            return result

        logger.error(f"{f.__name__} failed, {status=}")
        _, msg = self.dll.GetErrorText(status, 0x09)  # 0x09: English
        raise PCanError(f"{f.__name__} failed, {msg.decode()}")

    @property
    def _dll_initialize(self) -> typing.Callable:
        return [self.dll.Initialize, self.dll.InitializeFD][self.fd]

    def initialize(
        self,
        channel_handle: TPCANHandle,
        baud_rate: typing.Optional[bytes] = None,
        f_clock: int = 80000000,
        nom_brp: int = 2,
        nom_tseg1: int = 63,
        nom_tseg2: int = 16,
        nom_sjw: int = 16,
        data_brp: int = 2,
        data_tseg1: int = 15,
        data_tseg2: int = 4,
        data_sjw: int = 4,
    ) -> None:
        for channel in self.get_attached_channels():
            if channel_handle.value == channel.channel_handle:
                self.handle: TPCANHandle = channel_handle
                self._channel = channel
                logger.info(f"using channel {self.name}")
                break
        else:
            raise PCanError(f"channel not available")

        self.fd: bool = not isinstance(baud_rate, TPCANBaudrate)
        baud_rate: bytes = (
            baud_rate
            or (
                f"{f_clock=}, {nom_brp=}, {nom_tseg1=}, {nom_tseg2=}, "
                f"{nom_sjw=}, {data_brp=}, {data_tseg1=}, {data_tseg2=}, {data_sjw=}"
            ).encode()
        )
        return self._request(self._dll_initialize, self.handle, baud_rate)[0]

    def release(self) -> None:
        return self._request(self.dll.Uninitialize, self.handle)[0]

    @property
    def _dll_read(self) -> typing.Callable:
        return [self.dll.Read, self.dll.ReadFD][self.fd]

    def read_message(
        self,
        callbacks: typing.Optional[typing.Iterable[typing.Callable]] = None,
    ) -> typing.Tuple[TPCANStatus, TPCANTimestamp, typing.Union[TPCANMsg, TPCANMsgFD]]:
        status, msg, timestamp = self._dll_read(self.handle)
        for callback in callbacks or []:
            callback(status=status, timestamp=timestamp, msg=msg)
        return status, timestamp, msg

    def read_messages(self, callbacks: typing.Optional[typing.Iterable[typing.Callable]] = None) -> None:
        while True:
            status, msg, timestamp = self._dll_read(self.handle)
            if status & PCAN_ERROR_QRCVEMPTY:
                break
            if status & PCAN_ERROR_INITIALIZE:
                break
            if status != PCAN_ERROR_OK:
                logger.error(f"read_messages: 0x{status:05X}")
            for callback in callbacks or []:
                callback(status=status, timestamp=timestamp, msg=msg)

    def threading_read_message(
        self,
        callbacks: typing.Optional[typing.Iterable[typing.Callable]] = None,
    ) -> None:
        return RxThread(
            ch=self,
            kwargs=dict(
                callbacks=[*(callbacks or []), callback_rx],
            ),
        )

    @property
    def _dll_write(self) -> typing.Callable:
        return [self.dll.Write, self.dll.WriteFD][self.fd]

    def write_message(
        self,
        frame_id: int,
        data: typing.Optional[bytes] = None,
        callbacks: typing.Optional[typing.Iterable[typing.Callable]] = None,
    ) -> None:
        for callback in callbacks or []:
            if result := callback(frame_id=frame_id, data=data):
                frame_id, data = result
        msg = [TPCANMsg, TPCANMsgFD][self.fd]()
        msg.ID = frame_id
        msg.MSGTYPE = [PCAN_MESSAGE_STANDARD, PCAN_MESSAGE_FD][self.fd].value
        msg.DLC = SWAPPED_DLC_MAPPING[len(data)]
        for index, value in enumerate(data):
            msg.DATA[index] = value
        return self._request(self._dll_write, self.handle, msg)[0]

    def threading_write_message(
        self,
        interval: typing.Union[float, int],
        frame_id: int,
        callbacks: typing.Optional[typing.Iterable[typing.Callable]] = None,
    ) -> None:
        return TxThread(
            ch=self,
            interval=interval,
            kwargs=dict(
                frame_id=frame_id,
                callbacks=[callback_tx, *(callbacks or [])],
            ),
        )

    def get_attached_channels_count(self) -> int:
        return self._request(self.dll.GetValue, PCAN_NONEBUS, PCAN_ATTACHED_CHANNELS_COUNT)[0]

    def get_attached_channels(self) -> typing.Iterable[TPCANChannelInformation]:
        return self._request(self.dll.GetValue, PCAN_NONEBUS, PCAN_ATTACHED_CHANNELS)[0]

    def set_busoff_autoreset(self, state: PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF) -> None:
        return self._request(self.dll.SetValue, self.handle, PCAN_BUSOFF_AUTORESET, state)[0]

    def get_busoff_autoreset(self) -> PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF:
        return self._request(self.dll.GetValue, self.handle, PCAN_BUSOFF_AUTORESET)[0]

    def set_trace_status(self, state: PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF) -> None:
        return self._request(self.dll.SetValue, self.handle, PCAN_TRACE_STATUS, state)[0]

    def get_trace_status(self) -> None:
        return self._request(self.dll.GetValue, self.handle, PCAN_TRACE_STATUS)[0]

    def get_trace_size(self) -> None:
        return self._request(self.dll.GetValue, self.handle, PCAN_TRACE_SIZE)[0]

    def set_trace_size(self, size: int) -> None:
        """

        @param size: int, size(M)
        """
        return self._request(self.dll.SetValue, self.handle, PCAN_TRACE_SIZE, size)[0]

    def get_trace_configure(self) -> None:
        return self._request(self.dll.GetValue, self.handle, PCAN_TRACE_CONFIGURE)[0]

    def set_trace_configure(self, conf: int) -> None:
        """

        @param conf: int, using those as below:
            TRACE_FILE_SINGLE |
            TRACE_FILE_SEGMENTED |
            TRACE_FILE_DATE |
            TRACE_FILE_TIME |
            TRACE_FILE_OVERWRITE |
            TRACE_FILE_DATA_LENGTH
        @return:
        """
        return self._request(self.dll.SetValue, self.handle, PCAN_TRACE_CONFIGURE, conf)[0]

    def get_trace_location(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_TRACE_LOCATION)[0]

    def set_receive_event(self, event_handle: int) -> None:
        """

        @param event_handle: int, default 0, 0 means close
        @return:
        """
        return self._request(self.dll.SetValue, self.handle, PCAN_RECEIVE_EVENT, event_handle)[0]

    def get_api_version(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_API_VERSION)[0]

    def get_hardware_name(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_HARDWARE_NAME)[0]

    def get_channel_version(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_CHANNEL_VERSION)[0]

    def get_log_location(self) -> bytes:
        return self._request(self.dll.GetValue, PCAN_NONEBUS, PCAN_LOG_LOCATION)[0]

    def get_bitrate_info_fd(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_BITRATE_INFO_FD)[0]

    def get_firmware_version(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_FIRMWARE_VERSION)[0]

    def get_device_part_number(self) -> bytes:
        return self._request(self.dll.GetValue, self.handle, PCAN_DEVICE_PART_NUMBER)[0]

    def set_allow_status_frames(self, state: PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF) -> bytes:
        return self._request(self.dll.SetValue, self.handle, PCAN_ALLOW_STATUS_FRAMES, state)[0]

    def set_allow_rtr_frames(self, state: PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF) -> bytes:
        return self._request(self.dll.SetValue, self.handle, PCAN_ALLOW_RTR_FRAMES, state)[0]

    def set_allow_error_frames(self, state: PCAN_PARAMETER_ON | PCAN_PARAMETER_OFF) -> bytes:
        return self._request(self.dll.SetValue, self.handle, PCAN_ALLOW_ERROR_FRAMES, state)[0]

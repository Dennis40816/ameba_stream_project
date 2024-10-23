from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Type, Self
from abc import ABC, abstractmethod


class CameraBoard(Enum):
    AMEBA82_MINI = 0,


class CameraConnectionType(Enum):
    WIFI = 0,
    USB = 1


class CameraDataFormat(Enum):
    RTSP = 0,
    JPEG = 1

# store only config information


@dataclass
class CameraWirelessInfo:
    ip: Optional[str]
    port: Optional[int]
    rtsp_url: Optional[str]

    def __post_init__(self) -> None:
        self.check_valid_client_info_exist()

    def check_valid_client_info_exist(self) -> None:
        # TODO: currently, we only use ip and port. Domain can be added in the future
        if not self.ip or not self.port:
            raise ValueError(
                'Please provide enough wireless information: `ip` and `port`')

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    @staticmethod
    def bytes_to_wireless_info(bytes: bytes) -> Self:
        # TODO: impl
        pass

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    def wireless_info_to_bytes(self) -> bytes:
        # TODO: impl
        pass


@dataclass
class BasicCameraConfig(ABC):
    _brightness: Optional[int] = None
    _contrast: Optional[int] = None

    # TODO: add upper limit and lower limit bounds

    @property
    def brightness(self) -> Optional[int]:
        return self._brightness

    @brightness.setter
    def brightness(self, value: Optional[int]) -> None:
        if value is not None:
            if not (0 <= value <= 100):
                raise ValueError(
                    f"Brightness must be between 0 and 100, but got {value}.")
        self._brightness = value

    @property
    def contrast(self) -> Optional[int]:
        return self._contrast

    @contrast.setter
    def contrast(self, value: Optional[int]) -> None:
        if value is not None:
            if not (0 <= value <= 100):
                raise ValueError(
                    f"Contrast must be between 0 and 100, but got {value}.")
        self._contrast = value

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    @staticmethod
    @abstractmethod
    def bytes_to_config(self, bytes: bytes) -> Self:
        pass

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    @abstractmethod
    def config_to_bytes(self) -> bytes:
        pass


@dataclass
class BasicCameraInfo(ABC):
    # request without default value
    data_format: CameraDataFormat

    # optional without default value
    wireless_info: Optional[CameraWirelessInfo]

    # request with default value
    cmos_id: str = 'JX-F37P'
    connection_type: CameraConnectionType = CameraConnectionType.WIFI

    # optional with default value
    board: Optional[str] = CameraBoard.AMEBA82_MINI
    camera_config: Optional[Type[BasicCameraConfig]] = None

    # for list, dict use `field(default_factory=list)` to set default value

    def __post_init__(self) -> None:
        self.check_connection_type_requirement()
        self.check_data_format_requirement()

    def check_connection_type_requirement(self) -> None:
        # Wi-Fi connection
        if self.connection_type == CameraConnectionType.WIFI:
            if not self.wireless_info:
                raise ValueError(
                    "You're using Wi-Fi connection type, please also provides `wireless_info`")

    def check_data_format_requirement(self) -> None:
        if self.data_format == CameraDataFormat.RTSP:
            if not self.wireless_info.rtsp_url:
                raise ValueError(
                    "You're using RTSP data format, please also provides `rtsp_url` in `wireless_info`")

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    @staticmethod
    @abstractmethod
    def bytes_to_info(bytes: bytes) -> Self:
        pass

    # WARNING: SHOULD BE ARRANGED IN BIG ENDIAN
    @abstractmethod
    def info_to_bytes(self) -> bytes:
        pass

class AmebaCameraInfo(BasicCameraInfo):
  @staticmethod
  def bytes_to_info(bytes: bytes) -> Self:
    pass

'''
此處的 Camera 指的是 CAM + MCU 的總稱，並非僅是 CAM.
e.g., AmebaCamera -> Ameba82-MINI + JX-F37 CAM
'''


class BasicCamera(ABC):
    def __init__(self, camera_info: Type[BasicCameraInfo]) -> None:
        self.camera_info = camera_info

    def info_to_bytes(self) -> bytes:
        return self.camera_info.info_to_bytes()

    def bytes_to_info(self, bytes: bytes):
        # callee should be a static method
        return self.camera_info.bytes_to_info(bytes=bytes)

    def config_to_bytes(self) -> bytes:
        return self.camera_info.camera_config.config_to_bytes()

    def bytes_to_config(self, bytes: bytes):
        # callee should be a static method
        return self.camera_info.camera_config.bytes_to_config(bytes=bytes)

    def bytes_to_wireless_info(self):
        CameraWirelessInfo.bytes_to_wireless_info()


class AmebaCamera(BasicCamera):
  def __init__(self, camera_info: AmebaCameraInfo):
    pass

if __name__ == '__main__':
  obj = AmebaCameraInfo()
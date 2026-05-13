from typing import TypedDict
from enum import Enum


class CloudDeviceInfo(TypedDict):
    # {
    #     "statusTitle": "在线",
    #     "funcTitle": "",
    #     "aircornImgType": -1,
    #     "devSubTypeId": "72",
    #     "deviceName": "洗衣机",
    #     "usrLevel": "master",
    #     "roomId": "0000000",
    #     "roomName": "",
    #     "imgUrl": "http://images.psmartcloud.com/washer/body/body_washer_72.png",
    #     "bindTime": 1775302496,
    #     "isLogFunc": 0,
    #     "deviceMNO": "XQG100-E312",
    #     "shareDev": 0,
    #     "imgUrlsec": "",
    # }
    statusTitle: str
    funcTitle: str
    aircornImgType: int
    devSubTypeId: str
    deviceName: str
    usrLevel: str
    roomId: str
    roomName: str
    imgUrl: str
    bindTime: int
    isLogFunc: bool
    deviceMNO: str
    shareDev: bool
    imgUrlsec: str


class CachedSession(TypedDict):
    usrId: str
    SSID: str
    familyId: str
    realFamilyId: str
    devices: dict[str, CloudDeviceInfo]


class DeviceType(Enum):
    LAUNDRY = 600
    DRYER = 610

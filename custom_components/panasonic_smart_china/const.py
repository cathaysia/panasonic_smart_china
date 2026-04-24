from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACMode,
)

DOMAIN = "panasonic_smart_china"

CONF_USR_ID = "usrId"
CONF_DEVICE_ID = "deviceId"
CONF_TOKEN = "token"
CONF_SSID = "SSID"
CONF_SENSOR_ID = "sensor_entity_id"
CONF_CONTROLLER_MODEL = "controller_model"
CONF_DEVICE_CATEGORY = "device_category"
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_NAME = "device_name"
CONF_DEVICE_MODEL = "device_model"
CONF_DEVICE_SUBTYPE = "device_subtype"

DEVICE_TYPE_AIR_CONDITIONER = "air_conditioner"
DEVICE_TYPE_LAUNDRY = "laundry"
DEVICE_TYPE_UNKNOWN = "unknown"

DEVICE_CATEGORY_AIR_CONDITIONER = "0900"
DEVICE_CATEGORY_LAUNDRY = "0600"
DEVICE_CATEGORY_DRYER = "0610"

# Custom fan mode constants.
FAN_MIN = "Min"
FAN_MAX = "Max"
FAN_MUTE = "Quiet"

# Air conditioner controller profiles.
SUPPORTED_CONTROLLERS = {
    "CZ-RD501DW2": {
        "name": "松下风管机线控器 CZ-RD501DW2",
        "temp_scale": 2,
        "hvac_mapping": {
            HVACMode.COOL: 3,
            HVACMode.HEAT: 4,
            HVACMode.DRY: 2,
            HVACMode.AUTO: 0,
        },
        "fan_mapping": {
            FAN_AUTO: 10,
            FAN_MIN: 3,
            FAN_LOW: 4,
            FAN_MEDIUM: 5,
            FAN_HIGH: 6,
            FAN_MAX: 7,
        },
        "fan_payload_overrides": {
            FAN_MUTE: {"windSet": 10, "muteMode": 1},
        },
    }
}

LAUNDRY_DRUM_MODELS = {
    "XQG100-S1355",
    "XQG90-S9355",
    "XQG80-S8055",
    "XQG70-S7055",
}

LAUNDRY_DRUM_PROGRAMS = [
    (16, "节能洗"),
    (0, "一键智洗"),
    (1, "棉织物"),
    (2, "化纤"),
    (3, "羊毛"),
    (4, "丝绸/内衣"),
    (5, "运动服"),
    (6, "衬衫"),
    (7, "混合洗"),
    (8, "羽绒服"),
    (9, "筒洗净"),
    (10, "夜间洗"),
    (11, "大物"),
    (12, "浸泡洗"),
    (13, "超快速15"),
    (14, "快速"),
    (15, "除菌"),
    (17, "认证程序(能效)"),
    (18, "认证程序(A+)"),
]

LAUNDRY_TOP_LOAD_PROGRAMS = [
    (0, "一键智洗"),
    (1, "常用"),
    (2, "记忆"),
    (3, "浸泡洗"),
    (4, "毛毯"),
    (5, "节水漂"),
    (6, "超快速"),
    (7, "羊毛洗"),
    (8, "桶洗净"),
    (9, "认证程序(能效)"),
]

LAUNDRY_STATUS_LABELS = {
    0: "初期待机",
    1: "预约中",
    2: "运行中",
    3: "暂停中",
    4: "运行完成",
    5: "电源待机",
    6: "异常提醒",
    7: "本体离线",
    8: "本体操作中",
    9: "本体处理中",
    10: "关机中",
    11: "固件更新中",
    12: "固件更新完成",
}

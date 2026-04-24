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

WASHER_SPIN_SPEED_OPTIONS = {
    0: "500 转/分",
    1: "600 转/分",
    2: "700 转/分",
    3: "900 转/分",
    4: "1000 转/分",
    5: "1200 转/分",
    15: "--",
}

WASHER_WATER_LEVEL_OPTIONS = {
    1: "低",
    2: "中",
    4: "高",
    15: "--",
}

WASHER_TEMPERATURE_OPTIONS = {
    0: "冷水",
    1: "30°C",
    2: "40°C",
    3: "50°C",
    4: "60°C",
    5: "95°C",
    15: "--",
}

TOP_LOAD_WATER_LEVEL_OPTIONS = {
    1: "18L",
    3: "25L",
    4: "33L",
    5: "38L",
    6: "42L",
    7: "45L",
    8: "48L",
    9: "51L",
    10: "55L",
    12: "62L",
}

TOP_LOAD_RINSE_OPTIONS = {
    0: "无",
    1: "蓄水 1 次",
    2: "蓄水 2 次",
    3: "蓄水 3 次",
    4: "注水 1 次",
    5: "注水 2 次",
    6: "注水 3 次",
}

DRYER_DRY_SPEND_OPTIONS = {
    1: "1 级",
    2: "2 级",
    3: "3 级",
    4: "4 级",
    5: "5 级",
}

DRYER_DRY_MODE_OPTIONS = {
    1: "熨衣",
    2: "即穿",
    3: "入柜",
    4: "暖衣",
}

DRYER_DRY_TEMP_OPTIONS = {
    1: "40°C",
    2: "45°C",
    3: "50°C",
    4: "55°C",
    5: "60°C",
    6: "65°C",
}

DRYER_AIR_VOLUME_OPTIONS = {
    1: "1 档",
    2: "2 档",
    3: "3 档",
}

DRYER_DRY_TYPE_OPTIONS = {
    1: "低温烘干",
    2: "节能",
    3: "快速",
}

DRYER_FRESHEN_OPTIONS = {
    0: "关",
    2: "2 小时",
    3: "3 小时",
    4: "4 小时",
    5: "5 小时",
    6: "6 小时",
    7: "7 小时",
    8: "8 小时",
    9: "9 小时",
    10: "10 小时",
}

RAW_LAUNDRY_FIELD_LABELS = {
    "program": "程序 ID",
    "runingStage": "运行阶段",
    "runingStatus": "运行状态 ID",
    "timeDelayTotal": "预约时长",
    "timeDelayResidual": "预约剩余",
    "runingTimeTotal": "运行总时长",
    "runingTimeResidual": "运行剩余时长",
    "spendTime": "本次用时",
    "childLock": "童锁",
    "remoteEnable": "远程可用",
    "remoteStatus": "远程状态",
    "bodyOperating": "本体操作中",
    "bodyHandle": "本体处理中",
    "bodyMode": "本体模式",
    "gateStatus": "机门状态",
    "gateFault": "机门故障",
    "powerStatus": "电源状态",
    "temperature": "温度 ID",
    "spinSpeed": "转速 ID",
    "waterLevel": "水位 ID",
    "washCycleOrg": "洗涤行程",
    "rinseCycleOrg": "漂洗行程",
    "spinCycleOrg": "脱水行程",
    "washTime": "洗涤时间",
    "rinseTime": "漂洗设置",
    "spinTime": "脱水时间",
    "activeFoam": "活性泡",
    "agPlus": "光动银",
    "extraRinse": "额外漂洗",
    "preWash": "预洗",
    "easyIroning": "免熨烫",
    "drySpend": "干衣度 ID",
    "dryMode": "干衣模式 ID",
    "dryTemp": "干衣温度 ID",
    "dryTime": "干衣时间",
    "dryType": "干衣类型 ID",
    "airVo": "风量 ID",
    "delayClothes": "延时添衣",
    "freshenSetTime": "清新保持时长",
    "mute": "静音",
    "otaStatus": "OTA 状态",
}

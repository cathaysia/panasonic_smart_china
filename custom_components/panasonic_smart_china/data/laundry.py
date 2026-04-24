from __future__ import annotations

from typing import Any

from ..const import DEVICE_CATEGORY_DRYER
from .dryer import DRYER_OPTION_LABELS
from .washer import (
    DRUM_PROGRAMS,
    LAUNDRY_DRUM_MODELS,
    TOP_LOAD_OPTION_LABELS,
    TOP_LOAD_PROGRAMS,
    WASHER_OPTION_LABELS,
)

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


def is_top_load_laundry_model(model: str) -> bool:
    if not model:
        return False
    return model.upper() not in LAUNDRY_DRUM_MODELS


def get_laundry_program_map(model: str) -> dict[int, str]:
    programs = TOP_LOAD_PROGRAMS if is_top_load_laundry_model(model) else DRUM_PROGRAMS
    return {program_id: name for program_id, name in programs}


def get_laundry_status_label(status_code: int | None) -> str | None:
    if status_code is None:
        return None
    return LAUNDRY_STATUS_LABELS.get(status_code, str(status_code))


def get_laundry_option_label(device_category: str, model: str, field: str, value: Any) -> str | None:
    if value is None:
        return None

    if device_category == DEVICE_CATEGORY_DRYER:
        mapping = DRYER_OPTION_LABELS.get(field)
    elif is_top_load_laundry_model(model):
        mapping = TOP_LOAD_OPTION_LABELS.get(field)
    else:
        mapping = WASHER_OPTION_LABELS.get(field)

    if mapping is None:
        return None

    try:
        return mapping.get(int(value), str(value))
    except (TypeError, ValueError):
        return mapping.get(value, str(value))


def get_raw_laundry_field_label(field: str) -> str:
    return RAW_LAUNDRY_FIELD_LABELS.get(field, field)

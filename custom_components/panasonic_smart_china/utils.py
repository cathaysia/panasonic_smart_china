from __future__ import annotations

import hashlib
from typing import Any

from .const import (
    CONF_DEVICE_CATEGORY,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SUBTYPE,
    DEVICE_CATEGORY_AIR_CONDITIONER,
    DEVICE_CATEGORY_DRYER,
    DEVICE_CATEGORY_LAUNDRY,
    DEVICE_TYPE_AIR_CONDITIONER,
    DEVICE_TYPE_LAUNDRY,
    DEVICE_TYPE_UNKNOWN,
    DRYER_AIR_VOLUME_OPTIONS,
    DRYER_DRY_MODE_OPTIONS,
    DRYER_DRY_SPEND_OPTIONS,
    DRYER_DRY_TEMP_OPTIONS,
    DRYER_DRY_TYPE_OPTIONS,
    DRYER_FRESHEN_OPTIONS,
    LAUNDRY_DRUM_MODELS,
    LAUNDRY_DRUM_PROGRAMS,
    LAUNDRY_STATUS_LABELS,
    LAUNDRY_TOP_LOAD_PROGRAMS,
    RAW_LAUNDRY_FIELD_LABELS,
    TOP_LOAD_RINSE_OPTIONS,
    TOP_LOAD_WATER_LEVEL_OPTIONS,
    WASHER_SPIN_SPEED_OPTIONS,
    WASHER_TEMPERATURE_OPTIONS,
    WASHER_WATER_LEVEL_OPTIONS,
)


def parse_device_id(device_id: str) -> tuple[str, str, str] | None:
    """Parse Panasonic device ids in MAC_CATEGORY_SUFFIX form."""
    parts = device_id.upper().split("_")
    if len(parts) != 3:
        return None

    mac_part, category, suffix = parts
    if len(mac_part) < 6:
        return None

    return mac_part, category, suffix


def get_device_category(device_id: str) -> str | None:
    parsed = parse_device_id(device_id)
    if not parsed:
        return None
    return parsed[1]


def generate_device_token(device_id: str) -> str | None:
    """Generate Panasonic cloud token directly from device id."""
    parsed = parse_device_id(device_id)
    if not parsed:
        return None

    mac_part, category, suffix = parsed
    stoken = f"{mac_part[6:]}_{category}_{mac_part[:6]}"
    inner = hashlib.sha512(stoken.encode()).hexdigest()
    return hashlib.sha512(f"{inner}_{suffix}".encode()).hexdigest()


def infer_device_model(device_id: str, device_info: dict[str, Any]) -> str:
    return (
        str(
            device_info.get(CONF_DEVICE_MODEL)
            or device_info.get("devType")
            or device_info.get("deviceType")
            or device_info.get("productCode")
            or device_info.get("deviceCode")
            or device_info.get("productNo")
            or device_info.get("deviceModel")
            or device_id.split("_")[-1]
        )
        .strip()
        .upper()
    )


def infer_device_type(device_id: str, device_info: dict[str, Any]) -> str:
    category = get_device_category(device_id)
    if category == DEVICE_CATEGORY_AIR_CONDITIONER:
        return DEVICE_TYPE_AIR_CONDITIONER
    if category in (DEVICE_CATEGORY_LAUNDRY, DEVICE_CATEGORY_DRYER):
        return DEVICE_TYPE_LAUNDRY

    text = " ".join(
        str(
            device_info.get(key, "")
        )
        for key in (
            CONF_DEVICE_NAME,
            CONF_DEVICE_SUBTYPE,
            "devSubTypeId",
            "deviceType",
            "productName",
        )
    ).lower()

    if any(keyword in text for keyword in ("wash", "dryer", "dry", "洗", "烘", "干衣")):
        return DEVICE_TYPE_LAUNDRY

    return DEVICE_TYPE_UNKNOWN


def is_top_load_laundry_model(model: str) -> bool:
    if not model:
        return False
    return model.upper() not in LAUNDRY_DRUM_MODELS


def get_laundry_program_map(model: str) -> dict[int, str]:
    programs = LAUNDRY_TOP_LOAD_PROGRAMS if is_top_load_laundry_model(model) else LAUNDRY_DRUM_PROGRAMS
    return {program_id: name for program_id, name in programs}


def get_laundry_status_code(data: dict[str, Any]) -> int | None:
    error_code = data.get("_error_code")
    is_top_load = is_top_load_laundry_model(str(data.get(CONF_DEVICE_MODEL, "")))

    if is_top_load and data.get("gateFault"):
        return 6
    if data.get("otaStatus"):
        return 11
    if data.get("bodyOperating") or (not is_top_load and data.get("bodyMode")) or (
        is_top_load and data.get("bodyMode") and data.get("program") != 9
    ):
        return 8
    if data.get("bodyHandle"):
        return 9
    if error_code == "OFFLINE":
        return 7
    if error_code:
        return 6

    runing_stage = int(data.get("runingStage", 1))
    status = {
        0: 4,
        1: 0,
        2: 2,
        3: 1,
        4: 1,
        5: 5,
        6: 6,
        7: 10,
    }.get(runing_stage, 0)

    if int(data.get("runingStatus", 0)) == 0 and status == 2:
        status = 3

    if status == 0 and ((not is_top_load and data.get("program") in (17, 18)) or (is_top_load and data.get("program") == 9)):
        status = 8

    return status


def get_laundry_status_label(status_code: int | None) -> str | None:
    if status_code is None:
        return None
    return LAUNDRY_STATUS_LABELS.get(status_code, str(status_code))


def get_laundry_option_label(device_category: str, model: str, field: str, value: Any) -> str | None:
    if value is None:
        return None

    mapping = None
    if device_category == DEVICE_CATEGORY_DRYER:
        mapping = {
            "drySpend": DRYER_DRY_SPEND_OPTIONS,
            "dryMode": DRYER_DRY_MODE_OPTIONS,
            "dryTemp": DRYER_DRY_TEMP_OPTIONS,
            "airVo": DRYER_AIR_VOLUME_OPTIONS,
            "dryType": DRYER_DRY_TYPE_OPTIONS,
            "freshenSetTime": DRYER_FRESHEN_OPTIONS,
        }.get(field)
    elif is_top_load_laundry_model(model):
        mapping = {
            "waterLevel": TOP_LOAD_WATER_LEVEL_OPTIONS,
            "rinseTime": TOP_LOAD_RINSE_OPTIONS,
        }.get(field)
    else:
        mapping = {
            "spinSpeed": WASHER_SPIN_SPEED_OPTIONS,
            "waterLevel": WASHER_WATER_LEVEL_OPTIONS,
            "temperature": WASHER_TEMPERATURE_OPTIONS,
        }.get(field)

    if mapping is None:
        return None

    try:
        return mapping.get(int(value), str(value))
    except (TypeError, ValueError):
        return mapping.get(value, str(value))


def get_raw_laundry_field_label(field: str) -> str:
    return RAW_LAUNDRY_FIELD_LABELS.get(field, field)

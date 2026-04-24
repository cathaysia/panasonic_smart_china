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
)
from .data.laundry import (
    get_laundry_option_label,
    get_laundry_program_map,
    get_laundry_status_label,
    get_raw_laundry_field_label,
    is_top_load_laundry_model,
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

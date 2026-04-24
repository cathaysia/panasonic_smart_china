from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PanasonicApiClient
from .const import (
    CONF_DEVICE_CATEGORY,
    CONF_DEVICE_ID,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SUBTYPE,
    CONF_DEVICE_TYPE,
    CONF_SSID,
    CONF_TOKEN,
    CONF_USR_ID,
    DEVICE_CATEGORY_DRYER,
    DEVICE_CATEGORY_LAUNDRY,
)
from .utils import get_laundry_program_map, get_laundry_status_code, is_top_load_laundry_model

_LOGGER = logging.getLogger(__name__)

POLLING_INTERVAL = timedelta(seconds=15)


class PanasonicDeviceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.device_id = entry.data[CONF_DEVICE_ID]
        self.device_type = entry.data[CONF_DEVICE_TYPE]
        self.device_name = entry.data[CONF_DEVICE_NAME]
        self.device_model = entry.data.get(CONF_DEVICE_MODEL, "")
        self.device_subtype = entry.data.get(CONF_DEVICE_SUBTYPE, "")
        self.device_category = entry.data.get(CONF_DEVICE_CATEGORY, "")

        self.api = PanasonicApiClient(
            hass,
            entry.data[CONF_USR_ID],
            self.device_id,
            entry.data[CONF_TOKEN],
            entry.data[CONF_SSID],
            self.device_category,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"panasonic_smart_china_{self.device_id}",
            update_interval=POLLING_INTERVAL,
        )

    @property
    def has_program_select(self) -> bool:
        return bool(self.get_program_map())

    @property
    def supports_laundry_control(self) -> bool:
        return self.device_category == DEVICE_CATEGORY_LAUNDRY

    def get_program_map(self) -> dict[int, str]:
        if self.device_category != DEVICE_CATEGORY_LAUNDRY:
            return {}
        return get_laundry_program_map(self.device_model)

    @property
    def is_dryer(self) -> bool:
        return self.device_category == DEVICE_CATEGORY_DRYER

    @property
    def is_top_load(self) -> bool:
        return is_top_load_laundry_model(self.device_model)

    def get_status_code(self) -> int | None:
        if not self.data:
            return None
        status_data = {**self.data, CONF_DEVICE_MODEL: self.device_model}
        return get_laundry_status_code(status_data)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_laundry_status()
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    def _build_laundry_payload(self) -> dict[str, Any]:
        data = dict(self.data or {})
        is_top_load = is_top_load_laundry_model(self.device_model)
        power_status = 0 if int(data.get("runingStage", 5)) == 5 else 1

        if is_top_load:
            return {
                "powerStatus": power_status,
                "runingStatus": int(data.get("runingStatus", 0)),
                "program": int(data.get("program", 0)),
                "washTime": int(data.get("washTime", 0)),
                "rinseTime": int(data.get("rinseTime", 0)),
                "spinTime": int(data.get("spinTime", 0)),
                "waterLevel": int(data.get("waterLevel", 0)),
                "activeFoam": int(data.get("activeFoam", 0)),
                "agPlus": int(data.get("agPlus", 0)),
                "childLock": int(data.get("childLock", 0)),
                "timeDelayTotal": int(data.get("timeDelayTotal", 0)),
                "waterLevelswitch": int(data.get("waterLevelswitch", 0)),
            }

        pre_wash = int(data.get("preWash", 0))
        easy_ironing = int(data.get("easyIroning", 0))
        return {
            "powerStatus": power_status,
            "runingStatus": int(data.get("runingStatus", 0)),
            "program": int(data.get("program", 0)),
            "washCycle": int(data.get("washCycleOrg", data.get("washCycle", 0))),
            "rinseCycle": int(data.get("rinseCycleOrg", data.get("rinseCycle", 0))),
            "spinCycle": int(data.get("spinCycleOrg", data.get("spinCycle", 0))),
            "spinSpeed": int(data.get("spinSpeed", 0)),
            "waterLevel": int(data.get("waterLevel", 0)),
            "temperature": int(data.get("temperature", 0)),
            "activeFoam": int(data.get("activeFoam", 0)),
            "extraRinse": int(data.get("extraRinse", 0)),
            "preWash": pre_wash,
            "easyIroning": easy_ironing,
            "childLock": int(data.get("childLock", 0)),
            "timeDelayTotal": int(data.get("timeDelayTotal", 0)),
            "preWashCycle": pre_wash,
            "easyIroningCycle": easy_ironing,
        }

    async def async_set_laundry_status(self, changes: dict[str, Any]) -> None:
        payload = self._build_laundry_payload()
        payload.update(changes)

        if "preWash" in payload and "preWashCycle" not in payload:
            payload["preWashCycle"] = payload["preWash"]
        if "easyIroning" in payload and "easyIroningCycle" not in payload:
            payload["easyIroningCycle"] = payload["easyIroning"]

        await self.api.async_set_laundry_status(payload)
        await self.async_request_refresh()

    async def async_toggle_laundry_run_state(self) -> None:
        status_code = self.get_status_code()
        if status_code in (0, 3):
            await self.async_set_laundry_status({"runingStatus": 1})
        else:
            await self.async_set_laundry_status({"runingStatus": 0})

    async def async_set_laundry_power(self, powered_on: bool) -> None:
        await self.async_set_laundry_status({"powerStatus": 1 if powered_on else 0})

    async def async_select_laundry_program(self, program_id: int) -> None:
        await self.async_set_laundry_status({"program": program_id, "runingStatus": 0, "powerStatus": 1})

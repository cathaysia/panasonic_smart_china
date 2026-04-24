from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .entity import PanasonicCoordinatorEntity


NUMBER_FIELDS = {
    "washer": [
        ("timeDelayTotal", "预约时长", 0, 24, 1, "h"),
        ("washTime", "洗涤时间", 0, 120, 1, "min"),
        ("spinTime", "脱水时间", 0, 30, 1, "min"),
    ],
    "dryer": [
        ("timeDelayTotal", "预约时长", 0, 24, 1, "h"),
        ("dryTime", "干衣时间", 0, 240, 1, "min"),
        ("freshenSetTime", "清新保持", 0, 10, 1, "h"),
    ],
    "top_load": [
        ("timeDelayTotal", "预约时长", 0, 24, 1, "h"),
        ("washTime", "洗涤时间", 0, 120, 1, "min"),
        ("spinTime", "脱水时间", 0, 30, 1, "min"),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    key = "dryer" if coordinator.is_dryer else ("top_load" if coordinator.is_top_load else "washer")
    async_add_entities(
        PanasonicLaundryNumberEntity(coordinator, field, name, min_value, max_value, step, unit)
        for field, name, min_value, max_value, step, unit in NUMBER_FIELDS[key]
    )


class PanasonicLaundryNumberEntity(PanasonicCoordinatorEntity, NumberEntity):
    def __init__(
        self,
        coordinator,
        field: str,
        name: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.device_id}_{field}_number"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float | None:
        value = (self.coordinator.data or {}).get(self._field)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_laundry_status({self._field: int(value)})

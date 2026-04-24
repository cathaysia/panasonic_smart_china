from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .data.dryer import DRYER_NUMBER_FIELDS
from .data.washer import TOP_LOAD_NUMBER_FIELDS, WASHER_NUMBER_FIELDS
from .entity import PanasonicCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    fields = DRYER_NUMBER_FIELDS if coordinator.is_dryer else (
        TOP_LOAD_NUMBER_FIELDS if coordinator.is_top_load else WASHER_NUMBER_FIELDS
    )
    async_add_entities(
        PanasonicLaundryNumberEntity(coordinator, field, name, min_value, max_value, step, unit)
        for field, name, min_value, max_value, step, unit in fields
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

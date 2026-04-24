from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .entity import PanasonicCoordinatorEntity
from .utils import get_laundry_program_map, get_laundry_status_label


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    async_add_entities(
        [
            PanasonicLaundryStatusSensor(coordinator),
            PanasonicLaundryProgramSensor(coordinator),
            PanasonicLaundryErrorSensor(coordinator),
        ]
    )


class PanasonicLaundryStatusSensor(PanasonicCoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_status"
        self._attr_name = "运行状态"

    @property
    def native_value(self):
        return get_laundry_status_label(self.coordinator.get_status_code())


class PanasonicLaundryProgramSensor(PanasonicCoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_program"
        self._attr_name = "当前程序" if not coordinator.is_dryer else "当前模式"

    @property
    def native_value(self):
        program = (self.coordinator.data or {}).get("program")
        if program is None:
            return None

        return get_laundry_program_map(self.coordinator.device_model).get(int(program), str(program))


class PanasonicLaundryErrorSensor(PanasonicCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_error"
        self._attr_name = "错误码"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("_error_code")

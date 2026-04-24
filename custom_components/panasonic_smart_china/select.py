from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .entity import PanasonicCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY or not coordinator.has_program_select:
        return

    async_add_entities([PanasonicLaundryProgramSelect(coordinator)])


class PanasonicLaundryProgramSelect(PanasonicCoordinatorEntity, SelectEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_program_select"
        self._attr_name = "程序"

    @property
    def options(self):
        return list(self.coordinator.get_program_map().values())

    @property
    def current_option(self):
        program = (self.coordinator.data or {}).get("program")
        if program is None:
            return None
        return self.coordinator.get_program_map().get(int(program))

    async def async_select_option(self, option: str) -> None:
        for program_id, name in self.coordinator.get_program_map().items():
            if name == option:
                await self.coordinator.async_select_laundry_program(program_id)
                return

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .data.dryer import DRYER_SELECT_FIELDS
from .data.washer import TOP_LOAD_SELECT_FIELDS, WASHER_SELECT_FIELDS
from .entity import PanasonicCoordinatorEntity
from .utils import get_laundry_option_label


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    entities: list[SelectEntity] = []
    if coordinator.has_program_select:
        entities.append(PanasonicLaundryProgramSelect(coordinator))

    if coordinator.is_dryer:
        fields = DRYER_SELECT_FIELDS
    elif coordinator.is_top_load:
        fields = TOP_LOAD_SELECT_FIELDS
    else:
        fields = WASHER_SELECT_FIELDS

    entities.extend(PanasonicLaundryOptionSelect(coordinator, field, name, values) for field, name, values in fields)
    async_add_entities(entities)


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


class PanasonicLaundryOptionSelect(PanasonicCoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, field: str, name: str, values: list[int]) -> None:
        super().__init__(coordinator)
        self._field = field
        self._values = values
        self._attr_unique_id = f"{coordinator.device_id}_{field}_select"
        self._attr_name = name

    @property
    def options(self):
        return [
            get_laundry_option_label(self.coordinator.device_category, self.coordinator.device_model, self._field, value)
            for value in self._values
        ]

    @property
    def current_option(self):
        value = (self.coordinator.data or {}).get(self._field)
        return get_laundry_option_label(self.coordinator.device_category, self.coordinator.device_model, self._field, value)

    async def async_select_option(self, option: str) -> None:
        for value in self._values:
            if get_laundry_option_label(self.coordinator.device_category, self.coordinator.device_model, self._field, value) == option:
                await self.coordinator.async_set_laundry_status({self._field: value})
                return

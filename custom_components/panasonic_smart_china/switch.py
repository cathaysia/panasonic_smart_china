from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .data.dryer import DRYER_SWITCH_FIELDS
from .data.washer import WASHER_SWITCH_FIELDS
from .entity import PanasonicCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    entities: list[PanasonicLaundrySwitchEntity] = [
        PanasonicLaundrySwitchEntity(coordinator, "childLock", "童锁"),
    ]

    if coordinator.is_dryer:
        entities.extend(PanasonicLaundrySwitchEntity(coordinator, field, name) for field, name in DRYER_SWITCH_FIELDS)
    else:
        entities.extend(PanasonicLaundrySwitchEntity(coordinator, field, name) for field, name in WASHER_SWITCH_FIELDS)

    async_add_entities(entities)


class PanasonicLaundrySwitchEntity(PanasonicCoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, field: str, name: str) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.device_id}_{field}_switch"

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data or {}).get(self._field)
        if value is None:
            return None
        return bool(int(value))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_laundry_status({self._field: 1})

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_laundry_status({self._field: 0})

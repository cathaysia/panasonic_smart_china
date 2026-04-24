from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    if coordinator.device_type != DEVICE_TYPE_LAUNDRY:
        return

    async_add_entities(
        [
            PanasonicLaundryButton(coordinator, "start_pause", "开始/暂停"),
            PanasonicLaundryButton(coordinator, "power_on", "电源开"),
            PanasonicLaundryButton(coordinator, "power_off", "电源关"),
        ]
    )


class PanasonicLaundryButton(PanasonicCoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.device_id}_{key}"

    async def async_press(self) -> None:
        if self._key == "start_pause":
            await self.coordinator.async_toggle_laundry_run_state()
        elif self._key == "power_on":
            await self.coordinator.async_set_laundry_power(True)
        elif self._key == "power_off":
            await self.coordinator.async_set_laundry_power(False)

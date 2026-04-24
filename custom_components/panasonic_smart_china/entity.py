from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class PanasonicCoordinatorEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self.coordinator.device_id)},
            "name": self.coordinator.device_name,
            "manufacturer": "Panasonic",
            "model": self.coordinator.device_model or self.coordinator.device_subtype or self.coordinator.device_category,
        }

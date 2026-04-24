from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    FAN_AUTO,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_CONTROLLER_MODEL,
    CONF_SENSOR_ID,
    DEVICE_TYPE_AIR_CONDITIONER,
    FAN_MUTE,
    SUPPORTED_CONTROLLERS,
)
from .entity import PanasonicCoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    if coordinator.device_type != DEVICE_TYPE_AIR_CONDITIONER:
        return
    async_add_entities([PanasonicACEntity(hass, coordinator, entry)])


class PanasonicACEntity(PanasonicCoordinatorEntity, ClimateEntity):
    def __init__(self, hass: HomeAssistant, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._sensor_id = entry.data.get(CONF_SENSOR_ID)
        model = entry.data.get(CONF_CONTROLLER_MODEL, "CZ-RD501DW2")
        self._profile = SUPPORTED_CONTROLLERS.get(model) or list(SUPPORTED_CONTROLLERS.values())[0]
        self._temp_scale = self._profile.get("temp_scale", 2)
        self._hvac_map = self._profile.get("hvac_mapping", {})
        self._fan_map = self._profile.get("fan_mapping", {})
        self._fan_overrides = self._profile.get("fan_payload_overrides", {})
        self._attr_unique_id = f"panasonic_{coordinator.device_id}"

    @property
    def supported_features(self):
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.FAN_MODE
        )

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def min_temp(self):
        return 16.0

    @property
    def max_temp(self):
        return 30.0

    @property
    def target_temperature_step(self):
        return 1.0

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, *self._hvac_map.keys()]

    @property
    def hvac_mode(self):
        data = self.coordinator.data or {}
        if data.get("runStatus") != 1:
            return HVACMode.OFF
        run_mode = data.get("runMode")
        for ha_mode, panasonic_mode in self._hvac_map.items():
            if panasonic_mode == run_mode:
                return ha_mode
        return HVACMode.OFF

    @property
    def fan_modes(self):
        return list(dict.fromkeys([*self._fan_map.keys(), *self._fan_overrides.keys()]))

    @property
    def fan_mode(self):
        data = self.coordinator.data or {}
        p_wind = data.get("windSet")
        p_mute = data.get("muteMode")

        if p_wind == 10 and p_mute == 1:
            return FAN_MUTE

        for name, value in self._fan_map.items():
            if value == p_wind:
                return name

        return FAN_AUTO

    @property
    def current_temperature(self):
        if not self._sensor_id:
            return None

        state = self._hass.states.get(self._sensor_id)
        if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                return float(state.state)
            except ValueError:
                return None
        return None

    @property
    def target_temperature(self):
        data = self.coordinator.data or {}
        return data.get("setTemperature", 52) / self._temp_scale

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_ac_status({"runStatus": 0})
            return

        p_mode = self._hvac_map.get(hvac_mode, 3)
        await self.coordinator.async_set_ac_status({"runStatus": 1, "runMode": p_mode})

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.coordinator.async_set_ac_status({"setTemperature": int(temp * self._temp_scale)})

    async def async_set_fan_mode(self, fan_mode):
        if fan_mode == FAN_MUTE:
            await self.coordinator.async_set_ac_status({"windSet": 10, "muteMode": 1})
            return

        wind_set = self._fan_map.get(fan_mode, 10)
        await self.coordinator.async_set_ac_status({"windSet": wind_set, "muteMode": 0})

    async def async_turn_on(self):
        await self.coordinator.async_set_ac_status({"runStatus": 1})

    async def async_turn_off(self):
        await self.coordinator.async_set_ac_status({"runStatus": 0})

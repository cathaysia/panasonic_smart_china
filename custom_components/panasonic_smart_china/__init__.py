from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_FAMILY_ID, CONF_REAL_FAMILY_ID, CONF_SSID, CONF_USR_ID, DOMAIN
from .coordinator import PanasonicDeviceCoordinator

PLATFORMS = ["sensor", "button", "select", "switch", "number"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get("session"):
        domain_data["session"] = _restore_session_from_entries(hass)
    domain_data.setdefault("entries", {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get("session"):
        domain_data["session"] = _restore_session_from_entries(hass)
    domain_data.setdefault("entries", {})

    coordinator = PanasonicDeviceCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    domain_data["entries"][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unload_ok


def _restore_session_from_entries(hass: HomeAssistant) -> dict | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if not entry.data.get(CONF_USR_ID) or not entry.data.get(CONF_SSID):
            continue

        family_id = entry.data.get(CONF_FAMILY_ID)
        real_family_id = entry.data.get(CONF_REAL_FAMILY_ID)
        if family_id is None or real_family_id is None:
            continue

        return {
            CONF_USR_ID: entry.data[CONF_USR_ID],
            CONF_SSID: entry.data[CONF_SSID],
            CONF_FAMILY_ID: family_id,
            CONF_REAL_FAMILY_ID: real_family_id,
        }

    return None

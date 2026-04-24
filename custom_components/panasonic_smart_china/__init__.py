from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_FAMILY_ID, CONF_REAL_FAMILY_ID, CONF_SSID, CONF_USR_ID, DOMAIN
from .coordinator import PanasonicDeviceCoordinator

PLATFORMS = ["climate", "sensor", "button", "select", "switch", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning("[%s] async_setup start, existing domain_data keys=%s", DOMAIN, list(domain_data.keys()))
    if not domain_data.get("session"):
        _LOGGER.warning("[%s] async_setup restoring session from entries", DOMAIN)
        domain_data["session"] = _restore_session_from_entries(hass)
    _LOGGER.warning("[%s] async_setup session after restore=%s", DOMAIN, domain_data.get("session"))
    domain_data.setdefault("entries", {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning(
        "[%s] async_setup_entry start: entry_id=%s title=%s data=%s options=%s",
        DOMAIN,
        entry.entry_id,
        entry.title,
        dict(entry.data),
        dict(entry.options),
    )
    if not domain_data.get("session"):
        _LOGGER.warning("[%s] async_setup_entry restoring session from entries", DOMAIN)
        domain_data["session"] = _restore_session_from_entries(hass)
    _LOGGER.warning("[%s] async_setup_entry session after restore=%s", DOMAIN, domain_data.get("session"))
    domain_data.setdefault("entries", {})

    coordinator = PanasonicDeviceCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    domain_data["entries"][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.warning("[%s] async_unload_entry: entry_id=%s", DOMAIN, entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unload_ok


def _restore_session_from_entries(hass: HomeAssistant) -> dict | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        _LOGGER.warning(
            "[%s] checking entry for session restore: entry_id=%s data=%s",
            DOMAIN,
            entry.entry_id,
            dict(entry.data),
        )
        if not entry.data.get(CONF_USR_ID) or not entry.data.get(CONF_SSID):
            _LOGGER.warning(
                "[%s] skip entry %s: missing usrId or SSID", DOMAIN, entry.entry_id
            )
            continue

        family_id = entry.data.get(CONF_FAMILY_ID)
        real_family_id = entry.data.get(CONF_REAL_FAMILY_ID)
        if family_id is None or real_family_id is None:
            _LOGGER.warning(
                "[%s] skip entry %s: missing familyId or realFamilyId",
                DOMAIN,
                entry.entry_id,
            )
            continue

        session = {
            CONF_USR_ID: entry.data[CONF_USR_ID],
            CONF_SSID: entry.data[CONF_SSID],
            CONF_FAMILY_ID: family_id,
            CONF_REAL_FAMILY_ID: real_family_id,
        }
        _LOGGER.warning("[%s] restored session from entry %s: %s", DOMAIN, entry.entry_id, session)
        return session

    _LOGGER.warning("[%s] no restorable session found in config entries", DOMAIN)
    return None

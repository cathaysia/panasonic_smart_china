from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = [
    # "sensor", "button", "select", "switch", "number"
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(
        DOMAIN,
        {},
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Restore session info from `entry.data`
    """
    session_info = entry.data.get("session")
    hass.data[DOMAIN]["session"] = session_info

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

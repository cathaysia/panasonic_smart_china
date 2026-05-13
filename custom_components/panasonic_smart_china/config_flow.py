from __future__ import annotations

import logging
from collections.abc import Mapping
import typing

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.panasonic_smart_china.utils.types import (
    CachedSession,
    CloudDeviceInfo,
)

from .const import (
    CONF_DEVICE_CATEGORY,
    CONF_DEVICE_ID,
    CONF_FAMILY_ID,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SUBTYPE,
    CONF_DEVICE_TYPE,
    CONF_REAL_FAMILY_ID,
    CONF_SSID,
    CONF_TOKEN,
    CONF_USR_ID,
    DOMAIN,
)
from .utils.utils import (
    calc_login_token,
    generate_device_token,
    get_device_category,
    infer_device_model,
    infer_device_type,
)

_LOGGER = logging.getLogger(__name__)

URL_LOGIN = "https://app.psmartcloud.com/App/UsrLogin"
URL_GET_DEV = "https://app.psmartcloud.com/App/UsrGetBindDevInfo"
URL_GET_TOKEN = "https://app.psmartcloud.com/App/UsrGetToken"


class LoginData(typing.TypedDict):
    usrId: str | None
    SSID: str | None


class PanasonicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._login_data: LoginData = {
            "usrId": None,
            "SSID": None,
        }
        self._devices = {}
        self._temp_login_info = {}
        self._device_lookup = {}

    def _cache_session(
        self, usr_id: str, ssid: str, devices: dict | None = None
    ) -> None:
        session = {
            CONF_USR_ID: usr_id,
            CONF_SSID: ssid,
            CONF_FAMILY_ID: self._temp_login_info.get(CONF_FAMILY_ID),
            CONF_REAL_FAMILY_ID: self._temp_login_info.get(CONF_REAL_FAMILY_ID),
        }
        if devices is not None:
            session["devices"] = devices

        self.hass.data.setdefault(DOMAIN, {})["session"] = session

        # Persist the latest session fields so restarts do not fall back to stale SSIDs.
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_USERNAME) != self._login_data.get(
                CONF_USERNAME
            ) or entry.data.get(CONF_PASSWORD) != self._login_data.get(CONF_PASSWORD):
                continue

            updated_data = {
                **entry.data,
                CONF_USR_ID: usr_id,
                CONF_SSID: ssid,
                CONF_FAMILY_ID: self._temp_login_info.get(CONF_FAMILY_ID),
                CONF_REAL_FAMILY_ID: self._temp_login_info.get(CONF_REAL_FAMILY_ID),
            }
            self.hass.config_entries.async_update_entry(entry, data=updated_data)

    # Only called when setup plugin
    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USERNAME): str,
                        vol.Required(CONF_PASSWORD): str,
                    }
                ),
            )

        usr_id, ssid = await self._authenticate_full_flow(
            user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
        )

        self._login_data = {
            CONF_USR_ID: usr_id,
            CONF_SSID: ssid,
        }
        # update global cache
        session_info = {
            CONF_USERNAME: user_input[CONF_USERNAME],
            CONF_PASSWORD: user_input[CONF_PASSWORD],
            "session": {
                CONF_USR_ID: usr_id,
                CONF_SSID: ssid,
                "devices": [],
                "familyId": self._temp_login_info.get("familyId"),
                "realFamilyId": self._temp_login_info.get("realFamilyId"),
            },
        }

        self.hass.data[DOMAIN]["session"] = session_info

        return self.async_create_entry(
            title=f"Panasonic Smart China ({user_input[CONF_USERNAME]})",
            data=session_info,
        )

    async def async_step_reconfigure(self, _user_input=None):
        domain_data = self.hass.data.get(DOMAIN, {})
        session_cache: CachedSession = domain_data.get("session")
        if session_cache is None:
            return self.async_abort(reason="no_session_cache")
        await self.async_step_device(session_cache["usrId"], session_cache["SSID"])

    async def async_step_device(self, usr_id: str, ssid: str):
        existing_ids = self._async_current_ids()

        available_devices = {}
        self._device_lookup = {}
        devices = await self._get_devices_with_ssid(usr_id, ssid)
        print(f"获取设备列表: {devices}")

        for device_id, info in devices.items():
            if f"panasonic_{device_id}" in existing_ids:
                continue

            label = f"{info.get('deviceName', device_id)} ({device_id})"
            available_devices[device_id] = label
            self._device_lookup[device_id] = info

        if not available_devices:
            return self.async_abort(reason="all_devices_configured")

        if len(available_devices) > 1:
            device_ids = list(available_devices)
            for extra_device_id in device_ids[1:]:
                await self._async_create_additional_entry(extra_device_id)
            primary_device_id = device_ids[0]
            primary_info = self._device_lookup.get(
                primary_device_id, self._devices.get(primary_device_id, {})
            )
            return self._create_device_entry(primary_device_id, primary_info)

    def _create_device_entry(self, selected_dev_id, dev_info):
        dev_name = dev_info.get("deviceName", "Panasonic Device")
        device_type = infer_device_type(selected_dev_id, dev_info)
        device_model = infer_device_model(selected_dev_id, dev_info)
        token = generate_device_token(selected_dev_id)

        if not token:
            return self.async_abort(reason="token_generation_failed")

        data = {
            CONF_USR_ID: self._login_data[CONF_USR_ID],
            CONF_SSID: self._login_data[CONF_SSID],
            CONF_DEVICE_ID: selected_dev_id,
            CONF_TOKEN: token,
            CONF_DEVICE_CATEGORY: get_device_category(selected_dev_id),
            CONF_DEVICE_TYPE: device_type,
            CONF_DEVICE_NAME: dev_name,
            CONF_DEVICE_MODEL: device_model,
            CONF_DEVICE_SUBTYPE: str(dev_info.get("devSubTypeId", "")),
            CONF_FAMILY_ID: self._temp_login_info.get(CONF_FAMILY_ID),
            CONF_REAL_FAMILY_ID: self._temp_login_info.get(CONF_REAL_FAMILY_ID),
        }

        return self.async_create_entry(title=dev_name, data=data)

    async def async_step_import_device(
        self, import_data: Mapping[str, object] | None = None
    ):
        if not import_data:
            return self.async_abort(reason="cannot_connect")

        selected_dev_id = str(import_data[CONF_DEVICE_ID])
        if self._device_id_exists(selected_dev_id):
            return self.async_abort(reason="already_configured")

        dev_info = import_data.get("device_info", {})
        self._login_data = {
            CONF_USR_ID: str(import_data[CONF_USR_ID]),
            CONF_SSID: str(import_data[CONF_SSID]),
        }
        self._temp_login_info = {
            CONF_FAMILY_ID: import_data.get(CONF_FAMILY_ID),
            CONF_REAL_FAMILY_ID: import_data.get(CONF_REAL_FAMILY_ID),
        }
        return self._create_device_entry(selected_dev_id, dev_info)

    async def _async_create_additional_entry(self, device_id: str) -> None:
        if self._device_id_exists(device_id):
            return

        dev_info = self._device_lookup.get(device_id, self._devices.get(device_id, {}))
        await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import_device"},
            data={
                CONF_USR_ID: self._login_data[CONF_USR_ID],
                CONF_SSID: self._login_data[CONF_SSID],
                CONF_DEVICE_ID: device_id,
                CONF_FAMILY_ID: self._temp_login_info.get(CONF_FAMILY_ID),
                CONF_REAL_FAMILY_ID: self._temp_login_info.get(CONF_REAL_FAMILY_ID),
                "device_info": dev_info,
            },
        )

    def _device_id_exists(self, device_id: str) -> bool:
        return any(
            entry.data.get(CONF_DEVICE_ID) == device_id
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        )

    async def _get_devices_with_ssid(self, usr_id, ssid) -> dict[str, CloudDeviceInfo]:
        headers = {
            "User-Agent": "SmartApp",
            "Content-Type": "application/json",
            "Cookie": f"SSID={ssid}",
        }
        domain_data = self.hass.data.get(DOMAIN, {})
        session_cache = domain_data.get("session")
        if not session_cache or "familyId" not in session_cache:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    URL_GET_DEV,
                    json={
                        "id": 3,
                        "uiVersion": 4.0,
                        "params": {
                            "realFamilyId": session_cache["realFamilyId"],
                            "familyId": session_cache["familyId"],
                            "usrId": usr_id,
                        },
                    },
                    headers=headers,
                    ssl=False,
                ) as resp:
                    if resp.status != 200:
                        return None
                    dev_res = await resp.json()
                    if "results" not in dev_res:
                        return None
                    return {
                        dev["deviceId"]: dev["params"]
                        for dev in dev_res["results"]["devList"]
                    }
        except Exception:
            return None

    async def _authenticate_full_flow(self, username, password):
        headers = {"User-Agent": "SmartApp", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                URL_GET_TOKEN,
                json={"id": 1, "uiVersion": 4.0, "params": {"usrId": username}},
                headers=headers,
                ssl=False,
            ) as resp:
                data = await resp.json()
                if "results" not in data:
                    raise RuntimeError("GetToken failed")
                token_start = data["results"]["token"]

            final_token = calc_login_token(username, password, token_start)

            async with session.post(
                URL_LOGIN,
                json={
                    "id": 2,
                    "uiVersion": 4.0,
                    "params": {
                        "telId": "00:00:00:00:00:00",
                        "checkFailCount": 0,
                        "usrId": username,
                        "pwd": final_token,
                    },
                },
                headers=headers,
                ssl=False,
            ) as resp:
                login_res = await resp.json()
                if "results" not in login_res:
                    raise RuntimeError("Login failed")

                res = login_res["results"]
                real_usr_id = res["usrId"]
                ssid = res["ssId"]
                self._temp_login_info = {
                    CONF_REAL_FAMILY_ID: res[CONF_REAL_FAMILY_ID],
                    CONF_FAMILY_ID: res[CONF_FAMILY_ID],
                }

            return real_usr_id, ssid

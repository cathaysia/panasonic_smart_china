from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_CONTROLLER_MODEL,
    CONF_DEVICE_CATEGORY,
    CONF_DEVICE_ID,
    CONF_FAMILY_ID,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SUBTYPE,
    CONF_DEVICE_TYPE,
    CONF_REAL_FAMILY_ID,
    CONF_SENSOR_ID,
    CONF_SSID,
    CONF_TOKEN,
    CONF_USR_ID,
    DEVICE_TYPE_AIR_CONDITIONER,
    DEVICE_TYPE_UNKNOWN,
    DOMAIN,
    SUPPORTED_CONTROLLERS,
)
from .utils import generate_device_token, get_device_category, infer_device_model, infer_device_type

_LOGGER = logging.getLogger(__name__)

URL_LOGIN = "https://app.psmartcloud.com/App/UsrLogin"
URL_GET_DEV = "https://app.psmartcloud.com/App/UsrGetBindDevInfo"
URL_GET_TOKEN = "https://app.psmartcloud.com/App/UsrGetToken"


class PanasonicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._login_data = {}
        self._devices = {}
        self._temp_login_info = {}
        self._device_lookup = {}

    async def async_step_user(self, user_input=None):
        errors = {}

        domain_data = self.hass.data.get(DOMAIN, {})
        cached_session = domain_data.get("session")

        if cached_session:
            valid_devices = await self._get_devices_with_ssid(
                cached_session[CONF_USR_ID],
                cached_session[CONF_SSID],
            )
            if valid_devices:
                self._login_data = {
                    CONF_USR_ID: cached_session[CONF_USR_ID],
                    CONF_SSID: cached_session[CONF_SSID],
                }
                self._devices = valid_devices
                return await self.async_step_device()
            if DOMAIN in self.hass.data:
                self.hass.data[DOMAIN]["session"] = None

        if user_input is not None:
            try:
                usr_id, ssid, devices = await self._authenticate_full_flow(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )

                if not devices:
                    return self.async_abort(reason="no_devices_found")

                self._login_data = {CONF_USR_ID: usr_id, CONF_SSID: ssid}
                self._devices = devices
                self.hass.data.setdefault(DOMAIN, {})
                self.hass.data[DOMAIN]["session"] = {
                    CONF_USR_ID: usr_id,
                    CONF_SSID: ssid,
                    "devices": devices,
                    CONF_FAMILY_ID: self._temp_login_info.get(CONF_FAMILY_ID),
                    CONF_REAL_FAMILY_ID: self._temp_login_info.get(CONF_REAL_FAMILY_ID),
                }
                return await self.async_step_device()
            except Exception as err:
                _LOGGER.error("Login failed: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_device(self, user_input=None):
        errors = {}
        existing_ids = self._async_current_ids()

        available_devices = {}
        self._device_lookup = {}
        for device_id, info in self._devices.items():
            if f"panasonic_{device_id}" in existing_ids:
                continue

            device_type = infer_device_type(device_id, info)
            if device_type == DEVICE_TYPE_UNKNOWN:
                continue

            label = f"{info.get('deviceName', device_id)} ({device_id})"
            available_devices[device_id] = label
            self._device_lookup[device_id] = info

        if not available_devices:
            return self.async_abort(reason="all_devices_configured")

        ac_device_ids = {
            device_id
            for device_id, info in self._device_lookup.items()
            if infer_device_type(device_id, info) == DEVICE_TYPE_AIR_CONDITIONER
        }

        if user_input is None and len(available_devices) > 1 and not ac_device_ids:
            device_ids = list(available_devices)
            for extra_device_id in device_ids[1:]:
                await self._async_create_additional_entry(extra_device_id)
            primary_device_id = device_ids[0]
            primary_info = self._device_lookup.get(primary_device_id, self._devices.get(primary_device_id, {}))
            return self._create_device_entry(primary_device_id, primary_info)

        if user_input is not None:
            selected_dev_id = user_input[CONF_DEVICE_ID]
            dev_info = self._device_lookup.get(selected_dev_id, self._devices.get(selected_dev_id, {}))
            device_type = infer_device_type(selected_dev_id, dev_info)
            if device_type == DEVICE_TYPE_AIR_CONDITIONER:
                self.context[CONF_DEVICE_ID] = selected_dev_id
                return await self.async_step_air_conditioner_options()

            return self._create_device_entry(selected_dev_id, dev_info)

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): vol.In(available_devices),
                }
            ),
            errors=errors,
        )

    async def async_step_air_conditioner_options(self, user_input=None):
        errors = {}
        selected_dev_id = self.context.get(CONF_DEVICE_ID)
        if not selected_dev_id:
            return await self.async_step_device()

        dev_info = self._device_lookup.get(selected_dev_id, self._devices.get(selected_dev_id, {}))
        if infer_device_type(selected_dev_id, dev_info) != DEVICE_TYPE_AIR_CONDITIONER:
            return self._create_device_entry(selected_dev_id, dev_info)

        if user_input is not None:
            return self._create_device_entry(selected_dev_id, dev_info, user_input)

        controller_options = {key: value["name"] for key, value in SUPPORTED_CONTROLLERS.items()}
        return self.async_show_form(
            step_id="air_conditioner_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CONTROLLER_MODEL, default="CZ-RD501DW2"): vol.In(controller_options),
                    vol.Optional(CONF_SENSOR_ID): EntitySelector(EntitySelectorConfig(domain="sensor")),
                }
            ),
            errors=errors,
        )

    def _create_device_entry(self, selected_dev_id, dev_info, user_input=None):
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
        if device_type == DEVICE_TYPE_AIR_CONDITIONER and user_input is not None:
            data[CONF_CONTROLLER_MODEL] = user_input[CONF_CONTROLLER_MODEL]
            if user_input.get(CONF_SENSOR_ID):
                data[CONF_SENSOR_ID] = user_input[CONF_SENSOR_ID]

        return self.async_create_entry(title=dev_name, data=data)

    async def async_step_import_device(self, import_data: Mapping[str, object] | None = None):
        if not import_data:
            return self.async_abort(reason="cannot_connect")

        selected_dev_id = str(import_data[CONF_DEVICE_ID])
        if self._device_id_exists(selected_dev_id):
            return self.async_abort(reason="already_configured")

        dev_info = dict(import_data.get("device_info", {}))
        self._login_data = {
            CONF_USR_ID: import_data[CONF_USR_ID],
            CONF_SSID: import_data[CONF_SSID],
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
        if infer_device_type(device_id, dev_info) == DEVICE_TYPE_AIR_CONDITIONER:
            return

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
            entry.data.get(CONF_DEVICE_ID) == device_id for entry in self.hass.config_entries.async_entries(DOMAIN)
        )

    async def _get_devices_with_ssid(self, usr_id, ssid):
        headers = {"User-Agent": "SmartApp", "Content-Type": "application/json", "Cookie": f"SSID={ssid}"}
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
                    return {dev["deviceId"]: dev["params"] for dev in dev_res["results"]["devList"]}
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

            pwd_md5 = hashlib.md5(password.encode()).hexdigest().upper()
            inter_md5 = hashlib.md5((pwd_md5 + username).encode()).hexdigest().upper()
            final_token = hashlib.md5((inter_md5 + token_start).encode()).hexdigest().upper()

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

            headers["Cookie"] = f"SSID={ssid}"
            async with session.post(
                URL_GET_DEV,
                json={
                    "id": 3,
                    "uiVersion": 4.0,
                    "params": {
                        "realFamilyId": res["realFamilyId"],
                        "familyId": res["familyId"],
                        "usrId": real_usr_id,
                    },
                },
                headers=headers,
                ssl=False,
            ) as resp:
                dev_res = await resp.json()
                devices = {}
                if "results" in dev_res and "devList" in dev_res["results"]:
                    for dev in dev_res["results"]["devList"]:
                        devices[dev["deviceId"]] = dev["params"]
                return real_usr_id, ssid, devices

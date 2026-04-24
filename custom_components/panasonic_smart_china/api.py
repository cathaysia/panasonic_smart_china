from __future__ import annotations

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEVICE_CATEGORY_DRYER


URL_AC_SET = "https://app.psmartcloud.com/App/ACDevSetStatusInfoAW"
URL_AC_GET = "https://app.psmartcloud.com/App/ACDevGetStatusInfoAW"
URL_WASHER_GET_STATUS = "https://app.psmartcloud.com/App/WDevGetStatus"
URL_WASHER_GET_INFO = "https://app.psmartcloud.com/App/WDevGetStatusInfo"
URL_WASHER_GET_INFO_COMMON = "https://app.psmartcloud.com/App/WDevGetStatusInfoBD158"
URL_WASHER_SET = "https://app.psmartcloud.com/App/WDevSetStatusInfo"
URL_WASHER_SET_COMMON = "https://app.psmartcloud.com/App/WDevSetStatusInfoCommon"


class PanasonicApiClient:
    def __init__(
        self,
        hass: HomeAssistant,
        usr_id: str,
        device_id: str,
        token: str,
        ssid: str,
        device_category: str,
    ) -> None:
        self._hass = hass
        self._usr_id = usr_id
        self._device_id = device_id
        self._token = token
        self._ssid = ssid
        self._device_category = device_category

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X)",
            "xtoken": f"SSID={self._ssid}",
            "DNT": "1",
            "Origin": "https://app.psmartcloud.com",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def _post(self, url: str, payload: dict) -> dict:
        session = async_get_clientsession(self._hass)
        async with async_timeout.timeout(10):
            response = await session.post(url, json=payload, headers=self._headers, ssl=False)
            return await response.json()

    async def async_get_ac_status(self) -> dict:
        response = await self._post(
            URL_AC_GET,
            {"id": 100, "usrId": self._usr_id, "deviceId": self._device_id, "token": self._token},
        )
        return response.get("results", {})

    async def async_set_ac_status(self, params: dict) -> dict:
        return await self._post(
            URL_AC_SET,
            {
                "id": 200,
                "usrId": self._usr_id,
                "deviceId": self._device_id,
                "token": self._token,
                "params": params,
            },
        )

    async def async_get_laundry_status(self) -> dict:
        info_url = URL_WASHER_GET_INFO_COMMON if self._device_category == DEVICE_CATEGORY_DRYER else URL_WASHER_GET_INFO
        status_res = await self._post(
            URL_WASHER_GET_STATUS,
            {"id": 100, "usrId": self._usr_id, "deviceId": self._device_id, "token": self._token},
        )
        info_res = await self._post(
            info_url,
            {"id": 101, "usrId": self._usr_id, "deviceId": self._device_id, "token": self._token},
        )

        data = dict(info_res.get("results", {}))
        data["_error_code"] = status_res.get("results", {}).get("code")
        return data

    async def async_set_laundry_status(self, params: dict) -> dict:
        set_url = URL_WASHER_SET_COMMON if self._device_category == DEVICE_CATEGORY_DRYER else URL_WASHER_SET
        return await self._post(
            set_url,
            {
                "id": 200,
                "usrId": self._usr_id,
                "deviceId": self._device_id,
                "token": self._token,
                "params": params,
            },
        )

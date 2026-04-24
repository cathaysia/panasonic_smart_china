from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TYPE_LAUNDRY, DOMAIN
from .data.laundry import RAW_LAUNDRY_FIELD_LABELS
from .entity import PanasonicCoordinatorEntity
from .utils import get_laundry_option_label, get_laundry_program_map, get_laundry_status_label, get_raw_laundry_field_label


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
            PanasonicLaundryStatusSensor(coordinator),
            PanasonicLaundryProgramSensor(coordinator),
            PanasonicLaundryErrorSensor(coordinator),
            PanasonicLaundryRemainingTimeSensor(coordinator),
            PanasonicLaundrySpentTimeSensor(coordinator),
            *[
                PanasonicLaundryRawFieldSensor(coordinator, field)
                for field in sorted(RAW_LAUNDRY_FIELD_LABELS.keys())
            ],
        ]
    )


class PanasonicLaundryStatusSensor(PanasonicCoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_status"
        self._attr_name = "运行状态"

    @property
    def native_value(self):
        return get_laundry_status_label(self.coordinator.get_status_code())


class PanasonicLaundryProgramSensor(PanasonicCoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_program"
        self._attr_name = "当前程序" if not coordinator.is_dryer else "当前模式"

    @property
    def native_value(self):
        program = (self.coordinator.data or {}).get("program")
        if program is None:
            return None

        label = get_laundry_program_map(self.coordinator.device_model).get(int(program))
        return label or str(program)


class PanasonicLaundryErrorSensor(PanasonicCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_laundry_error"
        self._attr_name = "错误码"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("_error_code")


class PanasonicLaundryRemainingTimeSensor(PanasonicCoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_remaining_time"
        self._attr_name = "剩余时间"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        for field in ("runingTimeResidual", "timeDelayResidual"):
            if data.get(field) is not None:
                return data.get(field)
        return None


class PanasonicLaundrySpentTimeSensor(PanasonicCoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_spent_time"
        self._attr_name = "已用时间"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("spendTime")


class PanasonicLaundryRawFieldSensor(PanasonicCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, field: str) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_unique_id = f"{coordinator.device_id}_{field}_raw"
        self._attr_name = get_raw_laundry_field_label(field)

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self._field)
        if value is None:
            return None

        if self._field == "program":
            return get_laundry_program_map(self.coordinator.device_model).get(int(value), str(value))

        option_label = get_laundry_option_label(
            self.coordinator.device_category,
            self.coordinator.device_model,
            self._field,
            value,
        )
        return option_label if option_label is not None else value

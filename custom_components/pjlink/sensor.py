"""PJLink sensor platform."""

from __future__ import annotations

import logging

from aiopjlink.projector import Errors, Lamp, Power

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PJLINK_CLASS_2
from .coordinator import PJLinkCoordinator
from .entity import PJLinkEntity

_LOGGER = logging.getLogger(__name__)

# Map error category enums to friendly names
ERROR_CATEGORY_NAMES: dict[Errors.Category, str] = {
    Errors.Category.FAN: "Fan",
    Errors.Category.LAMP: "Lamp",
    Errors.Category.TEMP: "Temperature",
    Errors.Category.COVER: "Cover",
    Errors.Category.FILTER: "Filter",
    Errors.Category.OTHER: "Other",
}

ERROR_LEVEL_NAMES: dict[Errors.Level, str] = {
    Errors.Level.OK: "OK",
    Errors.Level.WARN: "Warning",
    Errors.Level.ERROR: "Error",
}

POWER_STATE_NAMES: dict[Power.State, str] = {
    Power.State.OFF: "Off",
    Power.State.ON: "On",
    Power.State.COOLING: "Cooling",
    Power.State.WARMING: "Warming",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PJLink sensor entities from a config entry."""
    coordinator: PJLinkCoordinator = entry.runtime_data
    entities: list[PJLinkSensorBase] = []

    # Power state sensor
    entities.append(PJLinkPowerStateSensor(coordinator))

    # Lamp sensors (one per lamp detected)
    if coordinator.data.lamps:
        for idx in range(len(coordinator.data.lamps)):
            entities.append(PJLinkLampHoursSensor(coordinator, idx))
            entities.append(PJLinkLampStatusSensor(coordinator, idx))

    # Error status sensors (one per category)
    if coordinator.data.errors:
        for category in coordinator.data.errors:
            entities.append(PJLinkErrorSensor(coordinator, category))

    # Class 2 sensors
    if coordinator.device_info.pjlink_class == PJLINK_CLASS_2:
        entities.append(PJLinkFilterHoursSensor(coordinator))
        entities.append(PJLinkInputResolutionSensor(coordinator))
        entities.append(PJLinkRecommendedResolutionSensor(coordinator))

    # PJLink class sensor (always useful)
    entities.append(PJLinkClassSensor(coordinator))

    async_add_entities(entities)


class PJLinkSensorBase(PJLinkEntity, SensorEntity):
    """Base class for PJLink sensors."""


class PJLinkPowerStateSensor(PJLinkSensorBase):
    """Sensor showing the detailed power state (off/on/cooling/warming)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the power state sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_power_state"
        self._attr_name = "Power state"

    @property
    def native_value(self) -> str:
        """Return the power state."""
        return POWER_STATE_NAMES.get(self.coordinator.data.power, "Unknown")


class PJLinkLampHoursSensor(PJLinkSensorBase):
    """Sensor showing lamp usage hours."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:lightbulb-on-outline"

    def __init__(self, coordinator: PJLinkCoordinator, lamp_index: int) -> None:
        """Initialize the lamp hours sensor."""
        super().__init__(coordinator)
        self._lamp_index = lamp_index
        lamp_num = lamp_index + 1
        self._attr_unique_id = f"{self._device_id}_lamp_{lamp_num}_hours"
        self._attr_name = f"Lamp {lamp_num} hours"

    @property
    def native_value(self) -> int | None:
        """Return the lamp hours."""
        lamps = self.coordinator.data.lamps
        if self._lamp_index < len(lamps):
            return lamps[self._lamp_index][0]
        return None


class PJLinkLampStatusSensor(PJLinkSensorBase):
    """Sensor showing lamp on/off status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:lightbulb"

    def __init__(self, coordinator: PJLinkCoordinator, lamp_index: int) -> None:
        """Initialize the lamp status sensor."""
        super().__init__(coordinator)
        self._lamp_index = lamp_index
        lamp_num = lamp_index + 1
        self._attr_unique_id = f"{self._device_id}_lamp_{lamp_num}_status"
        self._attr_name = f"Lamp {lamp_num} status"

    @property
    def native_value(self) -> str | None:
        """Return the lamp status."""
        lamps = self.coordinator.data.lamps
        if self._lamp_index < len(lamps):
            state = lamps[self._lamp_index][1]
            return "On" if state == Lamp.State.ON else "Off"
        return None


class PJLinkErrorSensor(PJLinkSensorBase):
    """Sensor showing error status per category."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: PJLinkCoordinator, category: Errors.Category
    ) -> None:
        """Initialize the error sensor."""
        super().__init__(coordinator)
        self._category = category
        cat_name = ERROR_CATEGORY_NAMES.get(category, category.value)
        self._attr_unique_id = f"{self._device_id}_error_{category.value}"
        self._attr_name = f"{cat_name} status"

    @property
    def native_value(self) -> str | None:
        """Return the error level for this category."""
        errors = self.coordinator.data.errors
        level = errors.get(self._category)
        if level is not None:
            return ERROR_LEVEL_NAMES.get(level, level.value)
        return None

    @property
    def icon(self) -> str:
        """Return an icon based on error level."""
        errors = self.coordinator.data.errors
        level = errors.get(self._category)
        if level == Errors.Level.ERROR:
            return "mdi:alert-circle"
        if level == Errors.Level.WARN:
            return "mdi:alert"
        return "mdi:check-circle-outline"


class PJLinkFilterHoursSensor(PJLinkSensorBase):
    """Sensor showing filter usage hours (Class 2)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the filter hours sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_filter_hours"
        self._attr_name = "Filter hours"

    @property
    def native_value(self) -> int | None:
        """Return filter usage hours."""
        return self.coordinator.data.filter_hours


class PJLinkInputResolutionSensor(PJLinkSensorBase):
    """Sensor showing current input resolution (Class 2)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the input resolution sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_input_resolution"
        self._attr_name = "Input resolution"

    @property
    def native_value(self) -> str | None:
        """Return the input resolution as a string."""
        res = self.coordinator.data.input_resolution
        if res:
            return f"{res[0]}x{res[1]}"
        return None


class PJLinkRecommendedResolutionSensor(PJLinkSensorBase):
    """Sensor showing recommended resolution (Class 2)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:monitor-star"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the recommended resolution sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_recommended_resolution"
        self._attr_name = "Recommended resolution"

    @property
    def native_value(self) -> str | None:
        """Return the recommended resolution as a string."""
        res = self.coordinator.data.recommended_resolution
        if res:
            return f"{res[0]}x{res[1]}"
        return None


class PJLinkClassSensor(PJLinkSensorBase):
    """Sensor showing the PJLink class of the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the PJLink class sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_pjlink_class"
        self._attr_name = "PJLink class"

    @property
    def native_value(self) -> str:
        """Return the PJLink class."""
        return self.coordinator.device_info.pjlink_class

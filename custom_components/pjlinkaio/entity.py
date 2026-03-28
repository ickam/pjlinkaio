"""Base entity for PJLink integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PJLinkCoordinator


class PJLinkEntity(CoordinatorEntity[PJLinkCoordinator]):
    """Base class for PJLink entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize a PJLink entity."""
        super().__init__(coordinator)

        info = coordinator.device_info
        host = coordinator.config_entry.data["host"]
        port = coordinator.config_entry.data.get("port", 4352)

        # Use serial number as identifier if available, else host:port
        if info.serial_number:
            self._device_id = info.serial_number
        else:
            self._device_id = f"{host}:{port}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=info.projector_name or f"PJLink {host}",
            manufacturer=info.manufacturer_name or None,
            model=info.product_name or None,
            serial_number=info.serial_number or None,
            sw_version=info.software_version or None,
        )

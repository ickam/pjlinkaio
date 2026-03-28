"""PJLink switch platform (freeze frame and video mute control)."""

from __future__ import annotations

import logging
from typing import Any

from aiopjlink.projector import Power

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PJLINK_CLASS_2
from .coordinator import PJLinkCoordinator
from .entity import PJLinkEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PJLink switch entities from a config entry."""
    coordinator: PJLinkCoordinator = entry.runtime_data

    entities: list[SwitchEntity] = []

    # Freeze switch is only available for Class 2 projectors
    if coordinator.device_info.pjlink_class == PJLINK_CLASS_2:
        entities.append(PJLinkFreezeSwitch(coordinator))

    # Video mute switch (available for all classes)
    entities.append(PJLinkVideoMuteSwitch(coordinator))

    async_add_entities(entities)


class PJLinkFreezeSwitch(PJLinkEntity, SwitchEntity):
    """Switch to control frame freeze on a PJLink Class 2 projector."""

    _attr_icon = "mdi:pause-box"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the freeze switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_freeze"
        self._attr_name = "Freeze"

    @property
    def is_on(self) -> bool | None:
        """Return true if the frame is frozen."""
        return self.coordinator.data.freeze

    @property
    def available(self) -> bool:
        """Only available when the projector is on."""
        if not super().available:
            return False
        return self.coordinator.data.power in (Power.State.ON, Power.State.WARMING)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Freeze the frame."""
        await self.coordinator.async_send_command(
            lambda link: link.freeze.set(True)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unfreeze the frame."""
        await self.coordinator.async_send_command(
            lambda link: link.freeze.set(False)
        )


class PJLinkVideoMuteSwitch(PJLinkEntity, SwitchEntity):
    """Switch to control video mute (blank screen)."""

    _attr_icon = "mdi:projector-off"

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the video mute switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_video_mute"
        self._attr_name = "Video mute"

    @property
    def is_on(self) -> bool:
        """Return true if video is muted (screen blanked)."""
        return self.coordinator.data.mute_video

    @property
    def available(self) -> bool:
        """Only available when the projector is on."""
        if not super().available:
            return False
        return self.coordinator.data.power in (Power.State.ON, Power.State.WARMING)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute video (blank screen)."""
        await self.coordinator.async_send_command(
            lambda link: link.mute.video(True)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute video (show image)."""
        await self.coordinator.async_send_command(
            lambda link: link.mute.video(False)
        )

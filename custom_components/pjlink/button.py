"""PJLink button platform (volume controls, Class 2)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiopjlink import PJLink
from aiopjlink.projector import Power

from homeassistant.components.button import ButtonEntity
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
    """Set up PJLink button entities from a config entry."""
    coordinator: PJLinkCoordinator = entry.runtime_data
    entities: list[ButtonEntity] = []

    # Volume buttons are only available for Class 2 projectors
    if coordinator.device_info.pjlink_class == PJLINK_CLASS_2:
        entities.extend(
            [
                PJLinkVolumeButton(
                    coordinator,
                    key="speaker_volume_up",
                    name="Speaker volume up",
                    icon="mdi:volume-plus",
                    command_func=lambda link: link.speaker.turn_up(),
                ),
                PJLinkVolumeButton(
                    coordinator,
                    key="speaker_volume_down",
                    name="Speaker volume down",
                    icon="mdi:volume-minus",
                    command_func=lambda link: link.speaker.turn_down(),
                ),
                PJLinkVolumeButton(
                    coordinator,
                    key="microphone_volume_up",
                    name="Microphone volume up",
                    icon="mdi:microphone-plus",
                    command_func=lambda link: link.microphone.turn_up(),
                ),
                PJLinkVolumeButton(
                    coordinator,
                    key="microphone_volume_down",
                    name="Microphone volume down",
                    icon="mdi:microphone-minus",
                    command_func=lambda link: link.microphone.turn_down(),
                ),
            ]
        )

    if entities:
        async_add_entities(entities)


class PJLinkVolumeButton(PJLinkEntity, ButtonEntity):
    """Button for PJLink volume step controls."""

    def __init__(
        self,
        coordinator: PJLinkCoordinator,
        *,
        key: str,
        name: str,
        icon: str,
        command_func: Callable[[PJLink], Awaitable[None]],
    ) -> None:
        """Initialize the volume button."""
        super().__init__(coordinator)
        self._command_func = command_func
        self._attr_unique_id = f"{self._device_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon

    @property
    def available(self) -> bool:
        """Only available when the projector is on."""
        if not super().available:
            return False
        return self.coordinator.data.power in (Power.State.ON, Power.State.WARMING)

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_send_command(self._command_func)

"""PJLink media player platform."""

from __future__ import annotations

import logging
from typing import Any

from aiopjlink.projector import Power, Sources

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PJLINK_CLASS_2
from .coordinator import PJLinkCoordinator, PJLinkState
from .entity import PJLinkEntity

_LOGGER = logging.getLogger(__name__)

# Map Sources.Mode enum to friendly names
SOURCE_MODE_NAMES: dict[str, str] = {
    "1": "RGB",
    "2": "VIDEO",
    "3": "DIGITAL",
    "4": "STORAGE",
    "5": "NETWORK",
    "6": "INTERNAL",
}


def _format_source_id(mode: Sources.Mode, index: str) -> str:
    """Create a source ID string like '11' from mode and index."""
    return f"{mode.value}{index}"


def _format_source_display(
    mode: Sources.Mode,
    index: str,
    source_names: dict[str, str],
) -> str:
    """Create a human-readable source name.

    If the projector provides a name (Class 2 INNM), use it.
    Otherwise, fall back to 'MODE INDEX' format (e.g. 'DIGITAL 1').
    """
    source_id = _format_source_id(mode, index)
    custom_name = source_names.get(source_id)
    if custom_name:
        return custom_name
    mode_name = SOURCE_MODE_NAMES.get(mode.value, mode.value)
    return f"{mode_name} {index}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PJLink media player from a config entry."""
    coordinator: PJLinkCoordinator = entry.runtime_data
    async_add_entities([PJLinkMediaPlayer(coordinator)])


class PJLinkMediaPlayer(PJLinkEntity, MediaPlayerEntity):
    """Representation of a PJLink projector as a media player."""

    _attr_name = None  # Use device name as entity name
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, coordinator: PJLinkCoordinator) -> None:
        """Initialize the PJLink media player."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_media_player"

    @property
    def state(self) -> MediaPlayerState:
        """Return the current state of the projector."""
        data: PJLinkState = self.coordinator.data
        if data.power in (Power.State.ON, Power.State.WARMING):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def is_volume_muted(self) -> bool:
        """Return true if audio is muted."""
        return self.coordinator.data.mute_audio

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        data: PJLinkState = self.coordinator.data
        if data.source_mode is None or data.source_index is None:
            return None
        return _format_source_display(
            data.source_mode,
            data.source_index,
            self.coordinator.device_info.source_names,
        )

    @property
    def source_list(self) -> list[str]:
        """Return the list of available input sources."""
        info = self.coordinator.device_info
        return [
            _format_source_display(mode, index, info.source_names)
            for mode, index in info.available_sources
        ]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data: PJLinkState = self.coordinator.data
        attrs: dict[str, Any] = {
            "pjlink_class": self.coordinator.device_info.pjlink_class,
        }
        if data.mute_video is not None:
            attrs["video_muted"] = data.mute_video
        return attrs

    def _get_source_mode_index(self, source_name: str) -> tuple[Sources.Mode, str]:
        """Resolve a display source name back to (Mode, index)."""
        info = self.coordinator.device_info
        for mode, index in info.available_sources:
            display = _format_source_display(mode, index, info.source_names)
            if display == source_name:
                return mode, index
        raise ValueError(f"Unknown source: {source_name}")

    async def async_turn_on(self) -> None:
        """Turn the projector on."""
        await self.coordinator.async_send_command(
            lambda link: link.power.turn_on()
        )

    async def async_turn_off(self) -> None:
        """Turn the projector off."""
        await self.coordinator.async_send_command(
            lambda link: link.power.turn_off()
        )

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute audio."""
        await self.coordinator.async_send_command(
            lambda link: link.mute.audio(mute)
        )

    async def async_select_source(self, source: str) -> None:
        """Select an input source."""
        mode, index = self._get_source_mode_index(source)
        await self.coordinator.async_send_command(
            lambda link: link.sources.set(mode, index)
        )

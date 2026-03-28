"""DataUpdateCoordinator for PJLink integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from aiopjlink import (
    PJLink,
    PJLinkConnectionClosed,
    PJLinkERR1,
    PJLinkERR3,
    PJLinkException,
    PJLinkNoConnection,
    PJLinkPassword,
    PJLinkProjectorError,
)
from aiopjlink.projector import Errors, Lamp, Power, Sources

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENCODING,
    DEFAULT_ENCODING,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    PJLINK_CLASS_2,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PJLinkDeviceInfo:
    """Static device information fetched once during setup."""

    projector_name: str = ""
    manufacturer_name: str = ""
    product_name: str = ""
    serial_number: str = ""
    software_version: str = ""
    pjlink_class: str = "1"
    available_sources: list[tuple[Sources.Mode, str]] = field(default_factory=list)
    source_names: dict[str, str] = field(default_factory=dict)


@dataclass
class PJLinkState:
    """Dynamic projector state fetched on each poll."""

    power: Power.State = Power.State.OFF
    source_mode: Sources.Mode | None = None
    source_index: str | None = None
    mute_video: bool = False
    mute_audio: bool = False
    lamps: list[tuple[int, Lamp.State]] = field(default_factory=list)
    errors: dict[Errors.Category, Errors.Level] = field(default_factory=dict)
    # Class 2 only
    freeze: bool | None = None
    filter_hours: int | None = None
    input_resolution: tuple[int, int] | None = None
    recommended_resolution: tuple[int, int] | None = None


class PJLinkCoordinator(DataUpdateCoordinator[PJLinkState]):
    """Coordinator that manages polling a PJLink projector."""

    config_entry: ConfigEntry
    device_info: PJLinkDeviceInfo

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"pjlink_{config_entry.data[CONF_HOST]}",
            config_entry=config_entry,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._host: str = config_entry.data[CONF_HOST]
        self._port: int = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        self._password: str | None = config_entry.data.get(CONF_PASSWORD)
        self._encoding: str = config_entry.data.get(CONF_ENCODING, DEFAULT_ENCODING)
        self.device_info = PJLinkDeviceInfo()

    def _create_connection(self) -> PJLink:
        """Create a new PJLink connection context manager."""
        return PJLink(
            address=self._host,
            port=self._port,
            password=self._password,
            timeout=DEFAULT_TIMEOUT,
            encoding=self._encoding,
        )

    async def _async_setup(self) -> None:
        """Fetch static device info on first refresh."""
        try:
            async with self._create_connection() as link:
                info = await link.info.table()

                self.device_info.projector_name = info.get("projector_name") or ""
                self.device_info.manufacturer_name = (
                    info.get("manufacturer_name") or ""
                )
                self.device_info.product_name = info.get("product_name") or ""
                self.device_info.serial_number = info.get("serial_number") or ""
                self.device_info.software_version = (
                    info.get("software_version") or ""
                )

                # Determine PJLink class
                try:
                    pjclass = await link.info.pjlink_class()
                    self.device_info.pjlink_class = pjclass.value
                except PJLinkException:
                    self.device_info.pjlink_class = "1"

                # Fetch available input sources
                try:
                    sources = await link.sources.available()
                    self.device_info.available_sources = sources
                except PJLinkException:
                    self.device_info.available_sources = []

                # If class 2, try to get source names
                if self.device_info.pjlink_class == PJLINK_CLASS_2:
                    for mode, index in self.device_info.available_sources:
                        try:
                            name = await link.sources.get_source_name(mode, index)
                            key = f"{mode.value}{index}"
                            if name:
                                self.device_info.source_names[key] = name
                        except PJLinkException:
                            pass

        except PJLinkPassword as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except (PJLinkNoConnection, PJLinkConnectionClosed, OSError) as err:
            raise UpdateFailed(f"Cannot connect to projector: {err}") from err
        except PJLinkException as err:
            raise UpdateFailed(f"PJLink error during setup: {err}") from err

    async def _async_update_data(self) -> PJLinkState:
        """Fetch dynamic state from the projector."""
        state = PJLinkState()

        try:
            async with self._create_connection() as link:
                # Power state (always available)
                try:
                    state.power = await link.power.get()
                except PJLinkERR3:
                    # Projector unavailable at this time
                    state.power = Power.State.OFF
                    return state

                # Only query further state if projector is on or warming up
                if state.power in (Power.State.ON, Power.State.WARMING):
                    # Current input source
                    try:
                        mode, index = await link.sources.get()
                        state.source_mode = mode
                        state.source_index = index
                    except PJLinkException:
                        pass

                    # Mute status
                    try:
                        video_muted, audio_muted = await link.mute.status()
                        state.mute_video = video_muted
                        state.mute_audio = audio_muted
                    except PJLinkException:
                        pass

                # Lamp status (available regardless of power state)
                try:
                    state.lamps = await link.lamps.status()
                except (PJLinkERR1, PJLinkException):
                    # No lamp or unsupported
                    pass

                # Error status
                try:
                    state.errors = await link.errors.query()
                except PJLinkException:
                    pass

                # Class 2 queries
                if self.device_info.pjlink_class == PJLINK_CLASS_2:
                    # Freeze status (only when on)
                    if state.power in (Power.State.ON, Power.State.WARMING):
                        try:
                            state.freeze = await link.freeze.get()
                        except PJLinkException:
                            pass

                    # Filter hours
                    try:
                        state.filter_hours = await link.filter.hours()
                    except (PJLinkERR1, PJLinkException):
                        pass

                    # Input resolution (only when on)
                    if state.power in (Power.State.ON, Power.State.WARMING):
                        try:
                            state.input_resolution = await link.sources.resolution()
                        except (PJLinkProjectorError, PJLinkException):
                            # No signal or unsupported
                            pass

                        try:
                            state.recommended_resolution = (
                                await link.sources.recommended_resolution()
                            )
                        except PJLinkException:
                            pass

        except PJLinkPassword as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except (PJLinkNoConnection, PJLinkConnectionClosed, OSError) as err:
            raise UpdateFailed(f"Cannot connect to projector: {err}") from err
        except PJLinkException as err:
            raise UpdateFailed(f"PJLink error: {err}") from err

        return state

    async def async_send_command(
        self, command_func: Any, *args: Any, **kwargs: Any
    ) -> None:
        """Send a command to the projector and refresh state.

        command_func should be an async callable that takes a PJLink instance.
        Example: coordinator.async_send_command(lambda link: link.power.turn_on())
        """
        try:
            async with self._create_connection() as link:
                await command_func(link, *args, **kwargs)
        except PJLinkPassword as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except (PJLinkNoConnection, PJLinkConnectionClosed, OSError) as err:
            raise UpdateFailed(f"Cannot connect to projector: {err}") from err
        except PJLinkException as err:
            raise UpdateFailed(f"PJLink command error: {err}") from err

        # Refresh state after command
        await self.async_request_refresh()

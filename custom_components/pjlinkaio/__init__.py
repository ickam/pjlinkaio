"""The PJLink AIO integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import PLATFORMS
from .coordinator import PJLinkCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up PJLink AIO integration.

    YAML import is intentionally disabled for the test domain.
    The legacy core 'pjlink' integration handles YAML configs.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PJLink AIO from a config entry."""
    coordinator = PJLinkCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a PJLink AIO config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

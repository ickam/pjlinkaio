"""The PJLink integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_ENCODING,
    DEFAULT_ENCODING,
    DEFAULT_PORT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import PJLinkCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up PJLink from YAML configuration (import only)."""
    # Look for legacy YAML media_player platform configs to import
    if "media_player" not in config:
        return True

    for platform_config in config["media_player"]:
        if platform_config.get("platform") != DOMAIN:
            continue

        _LOGGER.warning(
            "Configuration of PJLink via YAML is deprecated and will be removed "
            "in a future version. Please use the UI to set up PJLink integrations. "
            "Your existing YAML configuration for %s is being imported automatically",
            platform_config.get(CONF_HOST, "unknown"),
        )

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_HOST: platform_config.get(CONF_HOST, ""),
                    CONF_PORT: platform_config.get(CONF_PORT, DEFAULT_PORT),
                    CONF_PASSWORD: platform_config.get(CONF_PASSWORD),
                    CONF_ENCODING: platform_config.get(
                        CONF_ENCODING, DEFAULT_ENCODING
                    ),
                    CONF_NAME: platform_config.get(CONF_NAME),
                },
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PJLink from a config entry."""
    coordinator = PJLinkCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a PJLink config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

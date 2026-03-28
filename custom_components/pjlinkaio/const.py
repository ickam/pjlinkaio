"""Constants for the PJLink integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "pjlinkaio"

PLATFORMS: Final[list[Platform]] = [
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]

# Configuration keys
CONF_ENCODING: Final = "encoding"

# Defaults
DEFAULT_PORT: Final = 4352
DEFAULT_ENCODING: Final = "utf-8"
DEFAULT_TIMEOUT: Final = 10
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)

# PJLink class levels
PJLINK_CLASS_1: Final = "1"
PJLINK_CLASS_2: Final = "2"

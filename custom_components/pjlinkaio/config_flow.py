"""Config flow for PJLink integration."""

from __future__ import annotations

import logging
from typing import Any

from aiopjlink import PJLink, PJLinkNoConnection, PJLinkPassword
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT

from .const import (
    CONF_ENCODING,
    DEFAULT_ENCODING,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PJLINK_CLASS_2,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Optional(CONF_PASSWORD): str,
        vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): str,
    }
)


async def _async_try_connect(
    host: str,
    port: int,
    password: str | None,
    encoding: str,
) -> dict[str, Any]:
    """Try connecting to a PJLink projector and return device info.

    Raises PJLinkNoConnection or PJLinkPassword on failure.
    Returns a dict with projector_name, serial_number (if class 2), and pjlink_class.
    """
    async with PJLink(
        address=host,
        port=port,
        password=password,
        timeout=DEFAULT_TIMEOUT,
        encoding=encoding,
    ) as link:
        info = await link.info.table()
        try:
            pjclass = await link.info.pjlink_class()
            pjclass_str = pjclass.value
        except Exception:
            pjclass_str = "1"

        return {
            "projector_name": info.get("projector_name") or "",
            "manufacturer_name": info.get("manufacturer_name") or "",
            "product_name": info.get("product_name") or "",
            "serial_number": info.get("serial_number") or "",
            "software_version": info.get("software_version") or "",
            "pjlink_class": pjclass_str,
        }


class PJLinkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PJLink."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            password = user_input.get(CONF_PASSWORD)
            encoding = user_input.get(CONF_ENCODING, DEFAULT_ENCODING)

            try:
                device_info = await _async_try_connect(
                    host, port, password, encoding
                )
            except PJLinkNoConnection:
                errors["base"] = "cannot_connect"
            except PJLinkPassword:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during PJLink connection")
                errors["base"] = "unknown"
            else:
                # Use serial number as unique ID for Class 2, else host:port
                serial = device_info.get("serial_number")
                if serial:
                    unique_id = serial
                else:
                    unique_id = f"{host}:{port}"

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = (
                    device_info.get("projector_name")
                    or f"PJLink {host}"
                )

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PASSWORD: password,
                        CONF_ENCODING: encoding,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        host = import_data.get(CONF_HOST, "")
        port = import_data.get(CONF_PORT, DEFAULT_PORT)
        password = import_data.get(CONF_PASSWORD)
        encoding = import_data.get(CONF_ENCODING, DEFAULT_ENCODING)
        name = import_data.get(CONF_NAME)

        # Check if already configured by host:port
        self._async_abort_entries_match({CONF_HOST: host, CONF_PORT: port})

        try:
            device_info = await _async_try_connect(
                host, port, password, encoding
            )
        except (PJLinkNoConnection, PJLinkPassword, Exception):
            _LOGGER.warning(
                "Could not connect to PJLink projector at %s:%s during YAML import; "
                "creating entry anyway for later retry",
                host,
                port,
            )
            device_info = {}

        serial = device_info.get("serial_number")
        if serial:
            unique_id = serial
        else:
            unique_id = f"{host}:{port}"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        title = name or device_info.get("projector_name") or f"PJLink {host}"

        return self.async_create_entry(
            title=title,
            data={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_PASSWORD: password,
                CONF_ENCODING: encoding,
            },
        )

"""Config flow for the Marklife BLE integration."""

from __future__ import annotations

import dataclasses
import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_KEEP_CONNECTION,
    CONF_MODEL,
    CONF_PACKET_SIZE_CAP,
    CONF_STARVATION_MS,
    CONF_TICK_MS,
    DEFAULT_KEEP_CONNECTION,
    DEFAULT_PACKET_SIZE_CAP,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STARVATION_MS,
    DEFAULT_TICK_MS,
    DOMAIN,
)
from .marklife_ble import (
    advertisement_contradicts,
    find_profile_by_name,
    registered_profiles,
)

_LOGGER = logging.getLogger(__name__)

#: Bluetooth addresses are MACs on Linux; macOS hands out opaque UUIDs instead.
_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _model_selector() -> SelectSelector:
    """Build the model picker used when the name matched no profile."""
    options = [
        SelectOptionDict(
            value=profile.model_id,
            label=f"{profile.model_id.upper()} ({', '.join(profile.name_prefixes[:3])})",
        )
        for profile in registered_profiles()
        if profile.supported
    ]
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
    )


# Shown during setup: both are about how the printer fits into your network
# rather than how the protocol is driven, so they are answerable without knowing
# anything about the hardware.
SETUP_SCHEMA = {
    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
        NumberSelectorConfig(
            min=30, max=9999, step=1, mode=NumberSelectorMode.BOX,
            unit_of_measurement="seconds",
        )
    ),
    vol.Required(CONF_KEEP_CONNECTION, default=DEFAULT_KEEP_CONNECTION): bool,
}

# Protocol tuning. Every one has a working default in const.py, and ``_option()``
# in __init__.py falls back to it when the key is absent from both data and
# options -- so setup never asks. A first-time user cannot be expected to pick a
# credit starvation timeout; these belong in the Configure dialog, reached only
# when a printer is actually misbehaving.
TUNING_SCHEMA = {
    vol.Required(CONF_TICK_MS, default=DEFAULT_TICK_MS): NumberSelector(
        NumberSelectorConfig(
            min=0, max=200, step=1, mode=NumberSelectorMode.BOX,
            unit_of_measurement="milliseconds",
        )
    ),
    vol.Required(CONF_STARVATION_MS, default=DEFAULT_STARVATION_MS): NumberSelector(
        NumberSelectorConfig(
            min=500, max=10000, step=100, mode=NumberSelectorMode.BOX,
            unit_of_measurement="milliseconds",
        )
    ),
    vol.Required(CONF_PACKET_SIZE_CAP, default=DEFAULT_PACKET_SIZE_CAP): NumberSelector(
        NumberSelectorConfig(
            min=20, max=237, step=1, mode=NumberSelectorMode.BOX,
            unit_of_measurement="bytes",
        )
    ),
}

#: The Configure dialog exposes everything.
OPTIONS_SCHEMA = {**SETUP_SCHEMA, **TUNING_SCHEMA}


@dataclasses.dataclass
class Discovery:
    """A discovered Bluetooth printer."""

    name: str
    discovery_info: BluetoothServiceInfo


def _advertised_name(discovery_info: BluetoothServiceInfo) -> str | None:
    """Return the name Home Assistant's Bluetooth matchers saw.

    The manifest matchers run against ``service_info.name``, which prefers the
    advertised local name but falls back to a cached device name. Reading only
    ``advertisement.local_name`` here would abort a flow that the matcher had
    correctly triggered, on any advertisement that omits the local name.
    """
    return discovery_info.name or discovery_info.advertisement.local_name


class MarklifeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marklife BLE."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_device: Discovery | None = None
        self._discovered_devices: dict[str, Discovery] = {}
        self._unsupported_reason: str = ""

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle a printer found by the Bluetooth integration."""
        _LOGGER.debug("Discovered BT device: %s", discovery_info)
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = _advertised_name(discovery_info)
        _LOGGER.debug(
            "Advertised name %r, service UUIDs %s", name, discovery_info.service_uuids
        )
        profile = find_profile_by_name(name)
        if profile is None:
            return self.async_abort(reason="not_supported")
        if not profile.supported:
            # Recognised but unreachable -- say so instead of silently ignoring
            # a printer the user can see in the vendor app.
            self._unsupported_reason = profile.unsupported_reason
            return self.async_abort(reason="unsupported_transport")

        # Short prefixes like "M1-" or "S2-" can collide with unrelated hardware.
        # When the advertisement carries service UUIDs, require ours to be among
        # them so a name collision does not surface as a discovered printer.
        # Automatic discovery only -- the manual flow trusts the user's choice.
        if advertisement_contradicts(profile, discovery_info.service_uuids):
            _LOGGER.debug(
                "Ignoring %s (%s): advertises %s, expected service %s for profile %s",
                name,
                discovery_info.address,
                discovery_info.service_uuids,
                profile.service_uuid,
                profile.model_id,
            )
            return self.async_abort(reason="not_supported")

        self.context["title_placeholders"] = {"name": name}
        self._discovered_device = Discovery(name, discovery_info)
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the discovered printer and set options."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"], data=user_input
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
            data_schema=vol.Schema(SETUP_SCHEMA),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a printer from the devices Home Assistant can currently see."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]
            self.context["title_placeholders"] = {"name": discovery.name}
            self._discovered_device = discovery
            return self.async_create_entry(title=discovery.name, data=user_input)

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            name = _advertised_name(discovery_info)
            profile = find_profile_by_name(name)
            if profile is None:
                continue
            if not profile.supported:
                _LOGGER.info(
                    "Ignoring %s (%s): %s", name, address, profile.unsupported_reason
                )
                continue

            # Manual add stays permissive even when the advertisement omits our
            # service UUID -- the user picked this device deliberately. The log
            # line records what was actually advertised, which is the only way
            # to learn whether these printers put their service in the
            # advertisement at all.
            _LOGGER.debug(
                "Marklife candidate %s (%s) -> profile %s; advertises %s (expected %s)",
                name,
                address,
                profile.model_id,
                discovery_info.service_uuids,
                profile.service_uuid,
            )
            self._discovered_devices[address] = Discovery(name, discovery_info)

        if not self._discovered_devices:
            # Aborting here would be a dead end for a printer whose advertised
            # name none of the prefixes cover. Fall through to manual entry.
            return await self.async_step_manual()

        titles = {
            address: f"{discovery.name} ({discovery.discovery_info.address})"
            for address, discovery in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(titles)} | SETUP_SCHEMA
            ),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a printer whose advertised name matched no profile.

        The name is the only thing that identifies a Marklife model over the
        air -- there is no model-ID query -- so when it does not match, the user
        has to supply the model themselves. Without it there is no way to know
        which protocol, packet size, or darkness command to use.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            address = str(user_input[CONF_ADDRESS]).strip()
            # Only MAC-shaped input is validated: macOS hands out opaque UUIDs
            # instead of addresses, and those must pass through untouched.
            if ":" in address:
                address = address.upper()
                if not _MAC_RE.match(address):
                    errors[CONF_ADDRESS] = "invalid_address"
            if not address:
                errors[CONF_ADDRESS] = "invalid_address"
            if not errors:
                await self.async_set_unique_id(address, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                model_id = user_input[CONF_MODEL]
                return self.async_create_entry(
                    title=f"Marklife {model_id.upper()} ({address})",
                    data={**user_input, CONF_ADDRESS: address},
                )

        # Offer every visible BLE device, not just profile matches -- the whole
        # point of this step is that name matching came up empty.
        current_addresses = self._async_current_ids()
        visible = {
            info.address: f"{_advertised_name(info) or 'unknown'} ({info.address})"
            for info in async_discovered_service_info(self.hass)
            if info.address not in current_addresses
        }

        address_field: Any = vol.In(visible) if visible else str
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): address_field,
                    vol.Required(CONF_MODEL): _model_selector(),
                }
                | SETUP_SCHEMA
            ),
            errors=errors,
            description_placeholders={"count": str(len(visible))},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlowWithReload):
    """Handle option updates."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        suggested_values = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(OPTIONS_SCHEMA), suggested_values
            ),
        )

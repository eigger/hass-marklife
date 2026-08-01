"""The Marklife BLE integration."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
from datetime import timedelta

from bleak_retry_connector import close_stale_connections_by_address
from homeassistant.components import bluetooth
from homeassistant.components.image import Image
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_AREA_ID,
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
    EMPTY_PNG,
    PRINT_LOCK,
    ImageAndBLEData,
)
from .marklife_ble import BLEData, MarklifeDevice, MarklifeError
from .render import render_image

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)


def _option(entry: ConfigEntry, key: str, default):
    return entry.options.get(key, entry.data.get(key, default))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Marklife BLE printer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # One lock for the whole domain: overlapping BLE jobs contend for the same
    # adapter and for an ESP32 proxy's three connection slots.
    hass.data.setdefault(PRINT_LOCK, asyncio.Lock())
    address = entry.unique_id
    assert address is not None

    scan_interval = float(_option(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    keep_connection = bool(_option(entry, CONF_KEEP_CONNECTION, DEFAULT_KEEP_CONNECTION))
    tick_ms = int(_option(entry, CONF_TICK_MS, DEFAULT_TICK_MS))
    starvation_ms = int(_option(entry, CONF_STARVATION_MS, DEFAULT_STARVATION_MS))
    packet_size_cap = int(_option(entry, CONF_PACKET_SIZE_CAP, DEFAULT_PACKET_SIZE_CAP))

    await close_stale_connections_by_address(address)

    device = MarklifeDevice(
        address,
        # Set only when the printer was added by hand because its advertised
        # name matched no profile; otherwise the name resolves the model.
        model_id=entry.data.get(CONF_MODEL),
        keep_connection=keep_connection,
        # 0 means "trust the device profile".
        tick_ms=tick_ms or None,
        starvation_ms=starvation_ms,
        packet_size_cap=packet_size_cap,
    )

    async def _async_update_method() -> BLEData:
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        if ble_device is None:
            _LOGGER.warning(
                "Marklife printer %s is not currently visible; keeping last known data",
                address,
            )
            return device.ble_data

        try:
            return await device.update_device(ble_device)
        except Exception as err:  # noqa: BLE001 - never let polling kill the entry
            _LOGGER.warning(
                "Unable to poll %s: %s; keeping last known data", address, err
            )
            return device.ble_data

    coordinator: DataUpdateCoordinator[BLEData] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=scan_interval),
    )
    coordinator.data = device.ble_data
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        _LOGGER.warning(
            "Initial update failed for %s; entities start unavailable: %s",
            address,
            coordinator.last_exception,
        )

    image_coordinator: DataUpdateCoordinator[ImageAndBLEData] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
    )
    image_coordinator.async_set_updated_data(
        (Image(content_type="image/png", content=EMPTY_PNG), coordinator.data)
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "image_coordinator": image_coordinator,
        "device": device,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_print_service(hass)
    return True


def _async_register_print_service(hass: HomeAssistant) -> None:
    """Register ``marklife.print`` once for the whole domain.

    Registering inside the per-entry setup would rebind the handler on every
    reload, and each closure would capture one particular printer -- so with two
    printers configured, every call would go to whichever entry was set up last,
    regardless of the service target.
    """
    if hass.services.has_service(DOMAIN, "print"):
        return

    async def print_service(service: ServiceCall) -> ServiceResponse:
        entry_ids = _resolve_target_entry_ids(hass, service)
        results = [
            await _print_on_entry(hass, entry_id, service) for entry_id in entry_ids
        ]
        # One target keeps the flat response; a fan-out reports per printer.
        if len(results) == 1:
            return results[0]
        return {"results": results}

    hass.services.async_register(
        DOMAIN, "print", print_service, supports_response=SupportsResponse.OPTIONAL
    )


async def _print_on_entry(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> dict:
    """Render and print one label on one configured printer."""
    entry_data = hass.data[DOMAIN][entry_id]
    coordinator: DataUpdateCoordinator[BLEData] = entry_data["coordinator"]
    image_coordinator: DataUpdateCoordinator[ImageAndBLEData] = entry_data[
        "image_coordinator"
    ]
    device: MarklifeDevice = entry_data["device"]

    try:
        image = await hass.async_add_executor_job(
            render_image,
            entry_id,
            service,
            hass,
            device.ble_data.printhead_px,
        )
    except Exception as err:
        raise ServiceValidationError(f"Failed to create image: {err}") from err

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png = buffer.getvalue()

    image_coordinator.async_set_updated_data(
        (Image(content_type="image/png", content=png), coordinator.data)
    )
    image_data = f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}"

    if service.data.get("preview"):
        return {"image": image_data}

    ble_device = bluetooth.async_ble_device_from_address(hass, device.address)
    if ble_device is None:
        raise HomeAssistantError(
            f"Could not find printer {device.address} on your Bluetooth network"
        )

    # Serialise the BLE half domain-wide, not just per printer. Two printers
    # printing at once contend for the same adapter, and an ESP32 proxy only has
    # three connection slots -- overlapping jobs are how credit starvation and
    # half-printed labels happen. Rendering above stays parallel.
    lock: asyncio.Lock = hass.data[PRINT_LOCK]
    async with lock:
        try:
            result = await device.print_image(
                ble_device,
                image,
                density=int(service.data["density"]) if "density" in service.data else None,
                paper_type=service.data.get("paper_type", "gap"),
                copies=int(service.data.get("copies", 1)),
            )
        except (MarklifeError, RuntimeError) as err:
            raise HomeAssistantError(f"Failed to print: {err}") from err

    result["image"] = image_data
    return result


def _as_id_list(value) -> list[str]:
    """Normalise a target field that may be absent, a bare string, or a list.

    A YAML scalar target (``device_id: abc123``) arrives as a plain string, and
    feeding that straight into ``set()`` would iterate its characters.
    """
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _resolve_target_entry_ids(hass: HomeAssistant, service: ServiceCall) -> list[str]:
    """Work out which configured printers a service call is aimed at.

    Home Assistant merges ``target`` into ``service.data``, so device, area and
    entity selections arrive as plain fields. Targeting several printers at once
    is a normal thing to want -- an area with three of them prints on all three
    -- so this returns every match rather than insisting on exactly one. With a
    single printer configured the target may be omitted entirely.
    """
    configured: dict[str, dict] = hass.data.get(DOMAIN, {})
    if not configured:
        raise ServiceValidationError("No Marklife printer is configured")

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    device_ids = set(_as_id_list(service.data.get(ATTR_DEVICE_ID)))
    for area_id in _as_id_list(service.data.get(ATTR_AREA_ID)):
        device_ids.update(
            entry.id for entry in dr.async_entries_for_area(device_registry, area_id)
        )
    for entity_id in _as_id_list(service.data.get(ATTR_ENTITY_ID)):
        if (entity := entity_registry.async_get(entity_id)) and entity.device_id:
            device_ids.add(entity.device_id)

    entry_ids = [
        entry_id
        for device_id in sorted(device_ids)
        if (registry_entry := device_registry.async_get(device_id))
        for entry_id in registry_entry.config_entries
        if entry_id in configured
    ]

    if entry_ids:
        # dict.fromkeys keeps first-seen order while removing duplicates.
        return list(dict.fromkeys(entry_ids))
    if len(configured) == 1:
        return list(configured)
    raise ServiceValidationError(
        "Select which Marklife printer to print on -- more than one is configured"
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    # Drop the runtime first, then disconnect: by now the entities are gone, so
    # the connection callbacks have nobody left to notify. Both lookups tolerate
    # a missing entry so a half-finished setup can still be unloaded.
    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data and (device := entry_data.get("device")):
        await device.disconnect()

    # The service and the lock are domain-wide, so they outlive individual
    # entries. Removing one printer out of several must leave them in place --
    # the guard is "no printers left loaded", not "a printer was removed".
    if not hass.data.get(DOMAIN):
        if hass.services.has_service(DOMAIN, "print"):
            hass.services.async_remove(DOMAIN, "print")
        hass.data.pop(PRINT_LOCK, None)

    return True

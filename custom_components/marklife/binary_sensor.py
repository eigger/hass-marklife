"""Binary sensors for Marklife BLE printers.

The printer reports one condition at a time as ``[0xFF, code]`` rather than a
bitfield, so each fault sensor is on when that code is the current status. This
is unlike Niimbot, which reports lid/paper/RFID as independent flags in every
heartbeat.
"""

from __future__ import annotations

import dataclasses
import logging

from homeassistant import config_entries
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .entity import build_device_info, device_name
from .marklife_ble import BLEData, MarklifeDevice

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, kw_only=True)
class StatusBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Maps one printer status code onto a binary sensor."""

    status_value: str


STATUS_SENSORS: tuple[StatusBinarySensorEntityDescription, ...] = (
    StatusBinarySensorEntityDescription(
        key="out_of_paper",
        name="Out of Paper",
        status_value="out_of_paper",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:label-off-outline",
    ),
    StatusBinarySensorEntityDescription(
        key="cover_open",
        name="Cover Open",
        status_value="cover_open",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:printer-alert",
    ),
    StatusBinarySensorEntityDescription(
        key="overheating",
        name="Overheating",
        status_value="overheating",
        device_class=BinarySensorDeviceClass.HEAT,
        icon="mdi:thermometer-alert",
    ),
    StatusBinarySensorEntityDescription(
        key="low_battery",
        name="Low Battery",
        status_value="low_battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marklife binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator[BLEData] = data["coordinator"]
    device: MarklifeDevice = data["device"]

    entities: list[BinarySensorEntity] = [
        MarklifeConnectionBinarySensor(coordinator, device),
        MarklifePrintingBinarySensor(coordinator, device),
    ]
    entities.extend(
        MarklifeStatusBinarySensor(coordinator, description)
        for description in STATUS_SENSORS
    )
    async_add_entities(entities)


class MarklifeStatusBinarySensor(
    CoordinatorEntity[DataUpdateCoordinator[BLEData]], BinarySensorEntity
):
    """On when the printer's current status matches this condition."""

    _attr_has_entity_name = True
    entity_description: StatusBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        description: StatusBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_{description.key}"
        self._attr_device_info = build_device_info(ble_data)

    @property
    def is_on(self) -> bool | None:
        status = self.coordinator.data.sensors.get("status")
        if status is None:
            return None
        return status == self.entity_description.status_value


class _DeviceStateBinarySensor(
    CoordinatorEntity[DataUpdateCoordinator[BLEData]], BinarySensorEntity
):
    """Base for sensors driven by MarklifeDevice callbacks rather than polling."""

    _attr_has_entity_name = True
    _key: str

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        device: MarklifeDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._unsub = None
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_{self._key}"
        self._attr_device_info = build_device_info(ble_data)

    def _subscribe(self) -> None:
        """Attach to the device state change this sensor tracks."""
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._subscribe()

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def _handle_device_update(self) -> None:
        self.async_write_ha_state()


class MarklifeConnectionBinarySensor(_DeviceStateBinarySensor):
    """Whether a BLE connection to the printer is currently open."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:bluetooth-connect"
    _attr_name = "Connection"
    _key = "connection"

    def _subscribe(self) -> None:
        self._unsub = self._device.add_connection_listener(self._handle_device_update)

    @property
    def is_on(self) -> bool:
        return self._device.is_connected


class MarklifePrintingBinarySensor(_DeviceStateBinarySensor):
    """Whether a print job is in flight."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:printer-wireless"
    _attr_name = "Printing"
    _key = "printing"

    def _subscribe(self) -> None:
        self._unsub = self._device.add_printing_listener(self._handle_device_update)

    @property
    def is_on(self) -> bool:
        return self._device.is_printing

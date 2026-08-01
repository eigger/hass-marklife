"""Sensors for Marklife BLE printers."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .entity import build_device_info, device_name
from .marklife_ble import BLEData, MarklifeDevice

_LOGGER = logging.getLogger(__name__)

SENSORS: dict[str, SensorEntityDescription] = {
    "battery": SensorEntityDescription(
        key="battery",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "status": SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:printer-alert",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "out_of_paper",
            "cover_open",
            "overheating",
            "low_battery",
            "cover_closed",
        ],
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marklife sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator[BLEData] = data["coordinator"]
    device: MarklifeDevice = data["device"]

    entities: list[SensorEntity] = [
        MarklifeSensor(coordinator, description)
        for key, description in SENSORS.items()
        if key in coordinator.data.sensors
    ]
    entities.append(MarklifePrintDurationSensor(coordinator, device))

    async_add_entities(entities)


class MarklifeSensor(CoordinatorEntity[DataUpdateCoordinator[BLEData]], SensorEntity):
    """A value read straight from the BLEData snapshot."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_{entity_description.key}"
        self._attr_device_info = build_device_info(ble_data)

    @property
    def native_value(self) -> StateType:
        return self.coordinator.data.sensors.get(self.entity_description.key)


class MarklifePrintDurationSensor(
    CoordinatorEntity[DataUpdateCoordinator[BLEData]], SensorEntity
):
    """How long the current or last print job took."""

    _attr_has_entity_name = True
    _attr_name = "Print Duration"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        device: MarklifeDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._unsub_timer = None
        self._unsub_printing = None
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_print_duration"
        self._attr_device_info = build_device_info(ble_data)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub_printing = self._device.add_printing_listener(
            self._handle_printing_update
        )

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        if self._unsub_printing is not None:
            self._unsub_printing()
            self._unsub_printing = None
        self._stop_timer()

    def _start_timer(self) -> None:
        if self._unsub_timer is None:
            self._unsub_timer = async_track_time_interval(
                self.hass, self._tick, timedelta(seconds=1)
            )

    def _stop_timer(self) -> None:
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _tick(self, _now=None) -> None:
        self.async_write_ha_state()

    @callback
    def _handle_printing_update(self) -> None:
        if self._device.is_printing:
            self._start_timer()
        else:
            self._stop_timer()
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        return round(self._device.print_duration, 1)

    @property
    def extra_state_attributes(self) -> dict:
        duration = self._device.print_duration
        return {
            "formatted": f"{int(duration // 60):02d}:{int(duration % 60):02d}",
            "is_printing": self._device.is_printing,
        }

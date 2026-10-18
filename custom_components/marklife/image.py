"""Image platform -- shows the last label printed or previewed."""

from __future__ import annotations

import logging

from homeassistant.components.image import Image, ImageEntity, ImageEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util
from propcache.api import cached_property

from .const import DOMAIN, ImageAndBLEData
from .entity import build_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Marklife image entity."""
    assert config_entry.unique_id
    image_coordinator = hass.data[DOMAIN][config_entry.entry_id]["image_coordinator"]
    description = ImageEntityDescription(
        key="last_label_made",
        name="Last Label Made",
    )
    async_add_entities(
        [
            MarklifeImageEntity(
                hass, image_coordinator, description, config_entry.unique_id
            )
        ]
    )


class MarklifeImageEntity(
    CoordinatorEntity[DataUpdateCoordinator[ImageAndBLEData]], ImageEntity
):
    """The most recently rendered label."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator[ImageAndBLEData],
        entity_description: ImageEntityDescription,
        unique_id: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self.entity_description = entity_description
        self._attr_unique_id = f"{unique_id}_{entity_description.key}"
        self._attr_device_info = build_device_info(coordinator.data[1])
        self._cached_image: Image = coordinator.data[0]

    @cached_property
    def available(self) -> bool:
        """Always available -- it holds either a label or the empty placeholder."""
        return True

    @property
    def data(self) -> ImageAndBLEData:
        return self.coordinator.data

    def image(self) -> bytes | None:
        return self._cached_image.content

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("Updated label image")
        self._cached_image = self.data[0]
        self._attr_image_last_updated = dt_util.now()
        super()._handle_coordinator_update()

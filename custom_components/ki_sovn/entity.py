"""Felles entitetsbase."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import SovnCoordinator


class SovnEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: SovnCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=f"{coordinator.name} søvn",
            manufacturer="KI",
            model="Søvn-deteksjon",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

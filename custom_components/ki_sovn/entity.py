"""Felles entitetsbaser."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class KiEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, key: str, translation_key: str, device_suffix: str, model: str) -> None:
        self.coordinator = coordinator
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=f"{coordinator.name} {device_suffix}",
            manufacturer="KI",
            model=model,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class SovnEntity(KiEntity):
    def __init__(self, coordinator, key: str, translation_key: str) -> None:
        super().__init__(coordinator, key, translation_key, "søvn", "Søvndeteksjon")


class VekkingEntity(KiEntity):
    def __init__(self, coordinator, key: str, translation_key: str) -> None:
        super().__init__(coordinator, key, translation_key, "vekking", "Vekkealarm")

"""Time-entiteter for sovevindu og morgen."""
from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TIME_SETTINGS
from .coordinator import SovnCoordinator, _parse_time
from .entity import SovnEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SovnCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SettingTime(coordinator, key, tkey) for key, tkey in TIME_SETTINGS.items())


class SettingTime(SovnEntity, TimeEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, key, tkey) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = tkey
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"

    @property
    def native_value(self) -> time:
        return _parse_time(self.coordinator.cfg[self._key])

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_setting(self._key, value.strftime("%H:%M"))

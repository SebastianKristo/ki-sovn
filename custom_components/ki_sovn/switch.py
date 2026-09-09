"""Switch-entiteter: automatisk styring og dør-om-natta."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH_SETTINGS
from .coordinator import SovnCoordinator
from .entity import SovnEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SovnCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SettingSwitch(coordinator, key, tkey) for key, tkey in SWITCH_SETTINGS.items())


class SettingSwitch(SovnEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, key, tkey) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = tkey
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.cfg.get(self._key, True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(self._key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(self._key, False)

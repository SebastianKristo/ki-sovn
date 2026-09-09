"""Number-entiteter for innstillinger."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NUMBER_SETTINGS
from .coordinator import SovnCoordinator
from .entity import SovnEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SovnCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SettingNumber(coordinator, key, *spec) for key, spec in NUMBER_SETTINGS.items())


class SettingNumber(SovnEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, key, tkey, min_, max_, step, unit, scale) -> None:
        super().__init__(coordinator)
        self._key, self._scale = key, scale
        self._attr_translation_key = tkey
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = min_, max_, step
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float:
        return round(float(self.coordinator.cfg[self._key]) / self._scale, 2)

    async def async_set_native_value(self, value: float) -> None:
        stored = value * self._scale
        await self.coordinator.async_set_setting(self._key, round(stored, 3) if self._scale != 1 else int(value))

"""Number-entiteter for innstillinger (begge typer)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, KIND_PERSON, OPT_FADE, OPT_OFF_AFTER, PERSON_NUMBERS
from .entity import SovnEntity, VekkingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    if c.kind == KIND_PERSON:
        async_add_entities(OptNumber(SovnEntity, c, key, *spec, None) for key, spec in PERSON_NUMBERS.items())
        return
    async_add_entities([
        OptNumber(VekkingEntity, c, OPT_FADE, "fade_opp", 1, 60, 1, "min", 1, "mdi:brightness-auto"),
        OptNumber(VekkingEntity, c, OPT_OFF_AFTER, "av_etter", 5, 120, 5, "min", 1, "mdi:timer-off"),
    ])


def OptNumber(base, c, key, tkey, min_, max_, step, unit, scale, icon):  # noqa: N802
    class _Number(base, NumberEntity):
        _attr_entity_category = EntityCategory.CONFIG
        _attr_mode = NumberMode.SLIDER

        def __init__(self) -> None:
            super().__init__(c, key, tkey)
            self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = min_, max_, step
            self._attr_native_unit_of_measurement = unit
            if icon:
                self._attr_icon = icon

        @property
        def native_value(self) -> float:
            return round(float(self.coordinator.cfg[key]) / scale, 2)

        async def async_set_native_value(self, value: float) -> None:
            stored = value * scale
            await self.coordinator.async_set_setting(key, round(stored, 3) if scale != 1 else int(value))

    return _Number()

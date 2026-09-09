"""Time-entiteter: sovevindu/morgen (person) og vekketid per ukedag (vekking)."""
from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DAYS, DOMAIN, KIND_PERSON, PERSON_TIMES, opt_time
from .entity import SovnEntity, VekkingEntity
from .vekking import parse_time


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    if c.kind == KIND_PERSON:
        async_add_entities(OptTime(SovnEntity, c, key, tkey, None) for key, tkey in PERSON_TIMES.items())
    else:
        async_add_entities(OptTime(VekkingEntity, c, opt_time(d), d, "mdi:alarm") for d in DAYS)


def OptTime(base, c, key, tkey, icon):  # noqa: N802
    class _Time(base, TimeEntity):
        _attr_entity_category = EntityCategory.CONFIG

        def __init__(self) -> None:
            super().__init__(c, key, tkey)
            if icon:
                self._attr_icon = icon

        @property
        def native_value(self) -> time:
            return parse_time(self.coordinator.cfg[key])

        async def async_set_value(self, value: time) -> None:
            await self.coordinator.async_set_setting(key, value.strftime("%H:%M"))

    return _Time()

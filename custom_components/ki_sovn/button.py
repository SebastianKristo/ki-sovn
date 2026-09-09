"""Knapper: person «sett sover/våken», vekking «test/stopp»."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, KIND_PERSON
from .entity import SovnEntity, VekkingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    if c.kind == KIND_PERSON:
        async_add_entities([Btn(SovnEntity, c, "sett_sover", "mdi:sleep"), Btn(SovnEntity, c, "sett_vaaken", "mdi:sleep-off")])
    else:
        async_add_entities([Btn(VekkingEntity, c, "test", "mdi:play-circle"), Btn(VekkingEntity, c, "stopp", "mdi:stop-circle")])


def Btn(base, c, key, icon):  # noqa: N802
    class _Button(base, ButtonEntity):
        def __init__(self) -> None:
            super().__init__(c, key, key)
            self._attr_icon = icon

        async def async_press(self) -> None:
            if key == "test":
                await self.coordinator.async_run()
            elif key == "stopp":
                await self.coordinator.async_stop_sequence()
            elif key == "sett_sover":
                await self.coordinator.async_set_sleeping(True, "satt manuelt")
            else:
                await self.coordinator.async_set_sleeping(False, "satt manuelt")

    return _Button()

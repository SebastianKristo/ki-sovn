"""Brytere: person-innstillinger, vekking master/nattlampe/ukedager/person-kobling."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DAYS, DOMAIN, KIND_PERSON, OPT_MASTER, OPT_NIGHT_LIGHT_ON, OPT_ONLY_IF_ASLEEP, OPT_WAKE_PERSON,
    PERSON_SWITCHES, opt_active,
)
from .entity import SovnEntity, VekkingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    if c.kind == KIND_PERSON:
        async_add_entities(OptSwitch(SovnEntity, c, key, tkey, None, EntityCategory.CONFIG) for key, tkey in PERSON_SWITCHES.items())
        return
    ents = [OptSwitch(VekkingEntity, c, OPT_MASTER, "aktiv", "mdi:alarm-check", None),
            OptSwitch(VekkingEntity, c, OPT_NIGHT_LIGHT_ON, "nattlampe", "mdi:lamp", EntityCategory.CONFIG),
            OptSwitch(VekkingEntity, c, OPT_WAKE_PERSON, "vekk_person", "mdi:account-alert", EntityCategory.CONFIG),
            OptSwitch(VekkingEntity, c, OPT_ONLY_IF_ASLEEP, "bare_hvis_sover", "mdi:sleep", EntityCategory.CONFIG)]
    ents += [OptSwitch(VekkingEntity, c, opt_active(d), f"{d}_aktiv", "mdi:calendar-check", EntityCategory.CONFIG) for d in DAYS]
    async_add_entities(ents)


def OptSwitch(base, c, key, tkey, icon, category):  # noqa: N802 – fabrikk for begge basene
    class _Switch(base, SwitchEntity):
        def __init__(self) -> None:
            super().__init__(c, key, tkey)
            if icon:
                self._attr_icon = icon
            self._attr_entity_category = category

        @property
        def is_on(self) -> bool:
            return bool(self.coordinator.cfg.get(key, True if key == "enabled" else False))

        async def async_turn_on(self, **kwargs) -> None:
            await self.coordinator.async_set_setting(key, True)

        async def async_turn_off(self, **kwargs) -> None:
            await self.coordinator.async_set_setting(key, False)

    return _Switch()

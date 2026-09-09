"""KI Søvn & Vekking – søvndeteksjon per person og vekkealarm med gradvis lys."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_KIND, DOMAIN, KIND_VEKKING
from .sovn import SovnCoordinator
from .vekking import VekkingCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.NUMBER, Platform.TIME, Platform.SWITCH, Platform.BUTTON]


def kind_of(entry: ConfigEntry) -> str:
    return entry.data.get(CONF_KIND) or "person"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if kind_of(entry) == KIND_VEKKING:
        coordinator = VekkingCoordinator(hass, entry)
    else:
        coordinator = SovnCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator and coordinator.self_update:
        coordinator.self_update = False   # endring fra egen entitet – ingen reload nødvendig
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id).async_stop()
    return ok

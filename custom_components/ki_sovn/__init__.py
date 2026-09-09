"""KI Søvn – automatisk søvn/våken-deteksjon per person."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SovnCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.NUMBER, Platform.TIME, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SovnCoordinator(hass, entry)
    await coordinator.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator: SovnCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator and coordinator.self_update:
        coordinator.self_update = False   # endring fra egen entitet – ingen reload nødvendig
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coordinator: SovnCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.async_stop()
    return ok

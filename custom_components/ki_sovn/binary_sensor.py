"""Binary sensor: sover / våken."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SovnCoordinator
from .entity import SovnEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SovnCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SoverSensor(coordinator)])


class SoverSensor(SovnEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_translation_key = "sover"
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator: SovnCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sover"

    @property
    def is_on(self) -> bool:
        return self.coordinator.sleeping

    @property
    def extra_state_attributes(self) -> dict:
        c = self.coordinator
        return {
            "sannsynlighet": round(c.probability * 100, 1),
            "årsak": c.reason,
            "venter_på": c.pending,
            "armert": c.armed,
            **{f"obs_{k}": v for k, v in c.observations.items()},
        }

"""Sensor: søvn-sannsynlighet i prosent."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SovnCoordinator
from .entity import SovnEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SovnCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SannsynlighetSensor(coordinator)])


class SannsynlighetSensor(SovnEntity, SensorEntity):
    _attr_translation_key = "sannsynlighet"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:percent"

    def __init__(self, coordinator: SovnCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sannsynlighet"

    @property
    def native_value(self) -> float:
        return round(self.coordinator.probability * 100, 1)

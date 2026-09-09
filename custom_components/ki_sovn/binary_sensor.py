"""Binary sensors: person «sover», vekking «kjører»."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, KIND_PERSON
from .entity import SovnEntity, VekkingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SoverSensor(c)] if c.kind == KIND_PERSON else [Running(c)])


class SoverSensor(SovnEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:sleep"

    def __init__(self, c) -> None:
        super().__init__(c, "sover", "sover")

    @property
    def is_on(self) -> bool:
        return self.coordinator.sleeping

    @property
    def extra_state_attributes(self) -> dict:
        c = self.coordinator
        return {
            "integrasjon": DOMAIN,
            "type": "person",
            "navn": c.name,
            "prefix": c.prefix,
            "sannsynlighet": round(c.probability * 100, 1),
            "årsak": c.reason,
            "venter_på": c.pending,
            "armert": c.armed,
            "siden": c.last_change.isoformat() if c.last_change else None,
            "bryter": c.cfg.get("sleep_switch"),
            **{f"obs_{k}": v for k, v in c.observations.items()},
        }


class Running(VekkingEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, c) -> None:
        super().__init__(c, "kjorer", "kjorer")

    @property
    def is_on(self) -> bool:
        return self.coordinator.running

    @property
    def extra_state_attributes(self) -> dict:
        return {"fase": self.coordinator.phase}

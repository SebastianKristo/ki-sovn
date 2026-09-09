"""Sensorer: person «sannsynlighet», vekking «neste alarm»."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import CONF_PERSON, DOMAIN, KIND_PERSON, OPT_ONLY_IF_ASLEEP, OPT_WAKE_PERSON
from .entity import SovnEntity, VekkingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SannsynlighetSensor(c)] if c.kind == KIND_PERSON else [NextAlarm(c)])


class SannsynlighetSensor(SovnEntity, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:percent"

    def __init__(self, c) -> None:
        super().__init__(c, "sannsynlighet", "sannsynlighet")

    @property
    def native_value(self) -> float:
        return round(self.coordinator.probability * 100, 1)


class NextAlarm(VekkingEntity, SensorEntity):
    _attr_icon = "mdi:alarm"

    def __init__(self, c) -> None:
        super().__init__(c, "neste", "neste_alarm")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        @callback
        def _tick(_now) -> None:
            self.async_write_ha_state()

        self.async_on_remove(async_track_time_change(self.hass, _tick, second=1))

    @property
    def native_value(self) -> str:
        when, _ = self.coordinator.next_alarm()
        return when.strftime("%H:%M") if when else "Av"

    @property
    def extra_state_attributes(self) -> dict:
        c = self.coordinator
        when, day = c.next_alarm()
        return {
            "integrasjon": DOMAIN,
            "type": "vekking",
            "navn": c.name,
            "prefix": c.prefix,
            "neste_dag": day,
            "neste_tidspunkt": when.isoformat() if when else None,
            "betingelser": c.conditions,
            "betingelser_ok": c.conditions_ok(),
            "hopper_over": c.would_skip(),
            "person": c.cfg.get(CONF_PERSON),
            "person_sover": c.person_sleeping(),
            "vekk_person": bool(c.cfg.get(OPT_WAKE_PERSON)),
            "bare_hvis_sover": bool(c.cfg.get(OPT_ONLY_IF_ASLEEP)),
            "lys": c.lights,
            "sist_kjort": c.last_run.isoformat() if c.last_run else None,
            "sist_hoppet_over": c.last_skip,
        }

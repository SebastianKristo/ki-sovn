"""Config flow: velg «Person (søvn)» eller «Vekkealarm»."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AWAY_ROOM_MIN, CONF_BED, CONF_BEDTIME_END, CONF_BEDTIME_START, CONF_CONDITIONS, CONF_DOOR,
    CONF_DOOR_CLOSED_MIN, CONF_HEART_RATE, CONF_HOME_SWITCH, CONF_HR_AWAKE, CONF_HR_FRESH_MIN, CONF_HR_SLEEP,
    CONF_HR_WINDOW_MIN, CONF_KIND, CONF_LIGHTS, CONF_MORNING_AWAY_MIN, CONF_MORNING_FROM, CONF_MORNING_TO,
    CONF_NAME, CONF_NIGHT_DOOR_OK, CONF_NIGHT_LIGHT, CONF_OFF_DELAY, CONF_ON_DELAY, CONF_PERSON, CONF_PRESENCE,
    CONF_PRESENCE_HYST, CONF_PRIOR, CONF_SLEEP_SWITCH, CONF_START_PCT, CONF_THRESHOLD, CONF_WINDOW, DOMAIN,
    KIND_PERSON, KIND_VEKKING, PERSON_DEFAULTS, VEKKING_DEFAULTS,
)


def _ent(domain, multiple: bool = False, integration: str | None = None) -> selector.EntitySelector:
    cfg: dict[str, Any] = {"domain": domain, "multiple": multiple}
    if integration:
        cfg["integration"] = integration
    return selector.EntitySelector(selector.EntitySelectorConfig(**cfg))


def _num(min_: float, max_: float, step: float = 1, unit: str | None = None) -> selector.NumberSelector:
    cfg: dict[str, Any] = {"min": min_, "max": max_, "step": step, "mode": selector.NumberSelectorMode.BOX}
    if unit:
        cfg["unit_of_measurement"] = unit
    return selector.NumberSelector(selector.NumberSelectorConfig(**cfg))


def _sv(d: dict, k: str) -> dict:
    return {"suggested_value": d.get(k)}


# ------------------------------------------------------------------ person
def person_schema(d: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_NAME, default=d.get(CONF_NAME, "")): str,
        vol.Required(CONF_HOME_SWITCH, description=_sv(d, CONF_HOME_SWITCH)): _ent(["switch", "binary_sensor", "input_boolean"]),
        vol.Optional(CONF_SLEEP_SWITCH, description=_sv(d, CONF_SLEEP_SWITCH)): _ent(["switch", "input_boolean"]),
        vol.Optional(CONF_PRESENCE, description=_sv(d, CONF_PRESENCE)): _ent("binary_sensor"),
        vol.Optional(CONF_DOOR, description=_sv(d, CONF_DOOR)): _ent("binary_sensor"),
        vol.Optional(CONF_WINDOW, description=_sv(d, CONF_WINDOW)): _ent("binary_sensor"),
        vol.Optional(CONF_HEART_RATE, description=_sv(d, CONF_HEART_RATE)): _ent("sensor"),
        vol.Optional(CONF_BED, description=_sv(d, CONF_BED)): _ent("binary_sensor"),
    })


def tuning_schema(d: dict[str, Any]) -> vol.Schema:
    g = lambda k: d.get(k, PERSON_DEFAULTS[k])  # noqa: E731
    t = selector.TimeSelector
    return vol.Schema({
        vol.Required(CONF_BEDTIME_START, default=g(CONF_BEDTIME_START)): t(),
        vol.Required(CONF_BEDTIME_END, default=g(CONF_BEDTIME_END)): t(),
        vol.Required(CONF_NIGHT_DOOR_OK, default=g(CONF_NIGHT_DOOR_OK)): selector.BooleanSelector(),
        vol.Required(CONF_MORNING_FROM, default=g(CONF_MORNING_FROM)): t(),
        vol.Required(CONF_MORNING_TO, default=g(CONF_MORNING_TO)): t(),
        vol.Required(CONF_THRESHOLD, default=g(CONF_THRESHOLD)): _num(0.5, 0.99, 0.01),
        vol.Required(CONF_PRIOR, default=g(CONF_PRIOR)): _num(0.05, 0.6, 0.05),
        vol.Required(CONF_ON_DELAY, default=g(CONF_ON_DELAY)): _num(0, 60, 1, "min"),
        vol.Required(CONF_OFF_DELAY, default=g(CONF_OFF_DELAY)): _num(0, 60, 1, "min"),
        vol.Required(CONF_PRESENCE_HYST, default=g(CONF_PRESENCE_HYST)): _num(0, 120, 1, "min"),
        vol.Required(CONF_AWAY_ROOM_MIN, default=g(CONF_AWAY_ROOM_MIN)): _num(5, 180, 1, "min"),
        vol.Required(CONF_MORNING_AWAY_MIN, default=g(CONF_MORNING_AWAY_MIN)): _num(0, 60, 1, "min"),
        vol.Required(CONF_DOOR_CLOSED_MIN, default=g(CONF_DOOR_CLOSED_MIN)): _num(0, 120, 1, "min"),
        vol.Required(CONF_HR_SLEEP, default=g(CONF_HR_SLEEP)): _num(30, 100, 1, "bpm"),
        vol.Required(CONF_HR_AWAKE, default=g(CONF_HR_AWAKE)): _num(40, 150, 1, "bpm"),
        vol.Required(CONF_HR_FRESH_MIN, default=g(CONF_HR_FRESH_MIN)): _num(5, 240, 1, "min"),
        vol.Required(CONF_HR_WINDOW_MIN, default=g(CONF_HR_WINDOW_MIN)): _num(1, 60, 1, "min"),
    })


# ------------------------------------------------------------------ vekking
def vekking_schema(d: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_NAME, default=d.get(CONF_NAME, "Soverom")): str,
        vol.Required(CONF_LIGHTS, description=_sv(d, CONF_LIGHTS)): _ent("light", multiple=True),
        vol.Optional(CONF_NIGHT_LIGHT, description=_sv(d, CONF_NIGHT_LIGHT)): _ent("light"),
        vol.Optional(CONF_CONDITIONS, description=_sv(d, CONF_CONDITIONS)): _ent(["switch", "binary_sensor", "input_boolean", "person"], multiple=True),
        vol.Optional(CONF_PERSON, description=_sv(d, CONF_PERSON)): _ent("binary_sensor", integration=DOMAIN),
        vol.Required(CONF_START_PCT, default=d.get(CONF_START_PCT, VEKKING_DEFAULTS[CONF_START_PCT])): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=50, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="%")),
    })


class KiSovnConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(step_id="user", menu_options=[KIND_PERSON, KIND_VEKKING])

    async def async_step_person(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data = {**user_input, CONF_KIND: KIND_PERSON}
            return await self.async_step_tider()
        return self.async_show_form(step_id=KIND_PERSON, data_schema=person_schema({}))

    async def async_step_tider(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_{self._data[CONF_NAME].lower()}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data, options=user_input)
        return self.async_show_form(step_id="tider", data_schema=tuning_schema({}))

    async def async_step_vekking(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_vekking_{user_input[CONF_NAME].lower()}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"{user_input[CONF_NAME]} vekking", data={**user_input, CONF_KIND: KIND_VEKKING})
        return self.async_show_form(step_id=KIND_VEKKING, data_schema=vekking_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return KiSovnOptionsFlow(entry)


class KiSovnOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._data: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if self._entry.data.get(CONF_KIND) == KIND_VEKKING:
            return await self.async_step_vekking(user_input)
        return await self.async_step_person(user_input)

    async def async_step_person(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data = {**user_input, CONF_KIND: KIND_PERSON}
            return await self.async_step_tider()
        return self.async_show_form(step_id=KIND_PERSON, data_schema=person_schema(self._entry.data))

    async def async_step_tider(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.hass.config_entries.async_update_entry(self._entry, data=self._data, title=self._data[CONF_NAME])
            return self.async_create_entry(title="", data={**self._entry.options, **user_input})
        return self.async_show_form(step_id="tider", data_schema=tuning_schema(self._entry.options))

    async def async_step_vekking(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = {**user_input, CONF_KIND: KIND_VEKKING}
            self.hass.config_entries.async_update_entry(self._entry, data=data, title=f"{user_input[CONF_NAME]} vekking")
            return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(step_id=KIND_VEKKING, data_schema=vekking_schema(self._entry.data))

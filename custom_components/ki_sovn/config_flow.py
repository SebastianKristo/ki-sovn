"""Config flow for KI Søvn – én oppføring per person."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AWAY_ROOM_MIN,
    CONF_BED,
    CONF_BEDTIME_END,
    CONF_BEDTIME_START,
    CONF_DOOR,
    CONF_DOOR_CLOSED_MIN,
    CONF_HEART_RATE,
    CONF_HOME_SWITCH,
    CONF_HR_AWAKE,
    CONF_HR_FRESH_MIN,
    CONF_HR_SLEEP,
    CONF_HR_WINDOW_MIN,
    CONF_MORNING_AWAY_MIN,
    CONF_MORNING_FROM,
    CONF_MORNING_TO,
    CONF_NAME,
    CONF_NIGHT_DOOR_OK,
    CONF_OFF_DELAY,
    CONF_ON_DELAY,
    CONF_PRESENCE,
    CONF_PRESENCE_HYST,
    CONF_PRIOR,
    CONF_SLEEP_SWITCH,
    CONF_THRESHOLD,
    CONF_WINDOW,
    DEFAULTS,
    DOMAIN,
)


def _ent(domain: str | list[str]) -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def _num(min_: float, max_: float, step: float = 1, unit: str | None = None) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_, max=max_, step=step, mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


def _time() -> selector.TimeSelector:
    return selector.TimeSelector()


def person_schema(d: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=d.get(CONF_NAME, "")): str,
            vol.Required(CONF_HOME_SWITCH, default=d.get(CONF_HOME_SWITCH)): _ent(["switch", "binary_sensor", "input_boolean"]),
            vol.Optional(CONF_SLEEP_SWITCH, description={"suggested_value": d.get(CONF_SLEEP_SWITCH)}): _ent(["switch", "input_boolean"]),
            vol.Optional(CONF_PRESENCE, description={"suggested_value": d.get(CONF_PRESENCE)}): _ent("binary_sensor"),
            vol.Optional(CONF_DOOR, description={"suggested_value": d.get(CONF_DOOR)}): _ent("binary_sensor"),
            vol.Optional(CONF_WINDOW, description={"suggested_value": d.get(CONF_WINDOW)}): _ent("binary_sensor"),
            vol.Optional(CONF_HEART_RATE, description={"suggested_value": d.get(CONF_HEART_RATE)}): _ent("sensor"),
            vol.Optional(CONF_BED, description={"suggested_value": d.get(CONF_BED)}): _ent("binary_sensor"),
        }
    )


def tuning_schema(d: dict[str, Any]) -> vol.Schema:
    g = lambda k: d.get(k, DEFAULTS[k])  # noqa: E731
    return vol.Schema(
        {
            vol.Required(CONF_BEDTIME_START, default=g(CONF_BEDTIME_START)): _time(),
            vol.Required(CONF_BEDTIME_END, default=g(CONF_BEDTIME_END)): _time(),
            vol.Required(CONF_NIGHT_DOOR_OK, default=g(CONF_NIGHT_DOOR_OK)): selector.BooleanSelector(),
            vol.Required(CONF_MORNING_FROM, default=g(CONF_MORNING_FROM)): _time(),
            vol.Required(CONF_MORNING_TO, default=g(CONF_MORNING_TO)): _time(),
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
        }
    )


class KiSovnConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data = user_input
            return await self.async_step_tider()
        return self.async_show_form(step_id="user", data_schema=person_schema({}))

    async def async_step_tider(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_{self._data[CONF_NAME].lower()}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._data[CONF_NAME], data=self._data, options=user_input
            )
        return self.async_show_form(step_id="tider", data_schema=tuning_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return KiSovnOptionsFlow(entry)


class KiSovnOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._data: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data = user_input
            return await self.async_step_tider()
        return self.async_show_form(step_id="init", data_schema=person_schema(self._entry.data))

    async def async_step_tider(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self._entry, data=self._data, title=self._data[CONF_NAME]
            )
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="tider", data_schema=tuning_schema(self._entry.options))

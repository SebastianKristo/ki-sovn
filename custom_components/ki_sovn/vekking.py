"""Vekke-motor (kind = vekking): sjekker tid hvert minutt og kjører fade-sekvensen."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.util import dt as dt_util, slugify

from .const import (
    CONF_CONDITIONS, CONF_LIGHTS, CONF_NAME, CONF_NIGHT_LIGHT, CONF_PERSON, CONF_START_PCT,
    DAYS, DAY_NAMES, DOMAIN, KIND_VEKKING, OPT_FADE, OPT_MASTER, OPT_NIGHT_LIGHT_ON,
    OPT_OFF_AFTER, OPT_ONLY_IF_ASLEEP, OPT_WAKE_PERSON, VEKKING_DEFAULTS as DEFAULTS,
    opt_active, opt_time,
)

_LOGGER = logging.getLogger(__name__)


def parse_time(value: str) -> time:
    parts = [int(p) for p in str(value).split(":")]
    while len(parts) < 3:
        parts.append(0)
    return time(parts[0], parts[1], parts[2])


class VekkingCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.cfg: dict[str, Any] = {**DEFAULTS, **entry.data, **entry.options}
        self.name: str = self.cfg[CONF_NAME]
        self.kind = KIND_VEKKING
        self.prefix = slugify(f"{self.name} vekking")   # f.eks. soverom_vekking
        self.self_update = False
        self.running = False
        self.phase = "inaktiv"          # inaktiv | fader | lyser
        self.last_run: datetime | None = None
        self.last_skip: str | None = None
        self._task: asyncio.Task | None = None
        self._listeners: set[Callable[[], None]] = set()
        self._unsubs: list[Callable[[], None]] = []

    # ---------------------------------------------------------------- oppsett
    async def async_start(self) -> None:
        self._unsubs.append(async_track_time_change(self.hass, self._on_minute, second=0))
        ids = list(self.cfg.get(CONF_CONDITIONS) or [])
        if self.person_entity:
            ids.append(self.person_entity)
        if ids:
            self._unsubs.append(async_track_state_change_event(self.hass, ids, self._on_cond))
        self._notify()

    @callback
    def async_stop(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if self._task:
            self._task.cancel()

    @callback
    def async_add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(cb)
        return lambda: self._listeners.discard(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    async def async_set_setting(self, key: str, value: Any) -> None:
        self.cfg[key] = value
        self.self_update = True
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, key: value})
        self._notify()

    # ---------------------------------------------------------------- person-kobling
    @property
    def person_entity(self) -> str | None:
        return self.cfg.get(CONF_PERSON) or None

    def _person(self):
        """Søvn-koordinatoren til den koblede personen, hvis noen."""
        ent = self.person_entity
        if not ent:
            return None
        reg = er.async_get(self.hass).async_get(ent)
        if not reg or not reg.config_entry_id:
            return None
        c = self.hass.data.get(DOMAIN, {}).get(reg.config_entry_id)
        return c if c is not None and getattr(c, "kind", None) == "person" else None

    def person_sleeping(self) -> bool | None:
        ent = self.person_entity
        if not ent:
            return None
        st = self.hass.states.get(ent)
        return None if st is None or st.state in ("unknown", "unavailable") else st.state == "on"

    # ---------------------------------------------------------------- status
    @property
    def lights(self) -> list[str]:
        lights = list(self.cfg.get(CONF_LIGHTS) or [])
        nl = self.cfg.get(CONF_NIGHT_LIGHT)
        if nl and self.cfg.get(OPT_NIGHT_LIGHT_ON):
            lights.append(nl)
        return lights

    @property
    def conditions(self) -> list[str]:
        return list(self.cfg.get(CONF_CONDITIONS) or [])

    def conditions_ok(self) -> bool:
        return all(self.hass.states.is_state(e, "on") for e in self.conditions)

    def would_skip(self) -> str | None:
        """Hvorfor neste alarm ville blitt hoppet over akkurat nå (None = kjører)."""
        if not self.conditions_ok():
            return "betingelser"
        if self.cfg.get(OPT_ONLY_IF_ASLEEP) and self.person_sleeping() is False:
            return "våken"
        return None

    def next_alarm(self) -> tuple[datetime | None, str | None]:
        if not self.cfg.get(OPT_MASTER):
            return None, None
        now = dt_util.now()
        for offset in range(8):
            d = now + timedelta(days=offset)
            idx = d.weekday()
            day = DAYS[idx]
            if not self.cfg.get(opt_active(day)):
                continue
            t = parse_time(self.cfg.get(opt_time(day)))
            when = d.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if when > now:
                return when, DAY_NAMES[idx]
        return None, None

    # ---------------------------------------------------------------- trigger
    @callback
    def _on_cond(self, _event) -> None:
        self._notify()

    async def _on_minute(self, now: datetime) -> None:
        now = dt_util.as_local(now)
        day = DAYS[now.weekday()]
        if not self.cfg.get(OPT_MASTER) or not self.cfg.get(opt_active(day)):
            return
        t = parse_time(self.cfg.get(opt_time(day)))
        if (now.hour, now.minute) != (t.hour, t.minute):
            return
        skip = self.would_skip()
        if skip:
            self.last_skip = f"{now.strftime('%d.%m %H:%M')}: {skip}"
            _LOGGER.info("%s: alarm %s hoppet over (%s)", self.name, now.strftime("%H:%M"), skip)
            self._notify()
            return
        await self.async_run()

    # ---------------------------------------------------------------- sekvens
    async def async_run(self) -> None:
        if self.running:
            return
        self._task = self.hass.async_create_background_task(self._sequence(), f"ki_sovn vekking {self.name}")

    async def async_stop_sequence(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
        self.running = False
        self.phase = "inaktiv"
        if self.lights:
            await self.hass.services.async_call("light", "turn_off", {"entity_id": self.lights}, blocking=False)
        self._notify()

    async def _sequence(self) -> None:
        lights = self.lights
        if not lights:
            return
        fade_s = int(self.cfg.get(OPT_FADE)) * 60
        off_s = int(self.cfg.get(OPT_OFF_AFTER)) * 60
        start = int(self.cfg.get(CONF_START_PCT, 1))
        self.running = True
        self.last_run = dt_util.now()
        try:
            self.phase = "fader"; self._notify()
            await self.hass.services.async_call("light", "turn_on", {"entity_id": lights, "brightness_pct": start}, blocking=True)
            await asyncio.sleep(1)
            await self.hass.services.async_call(
                "light", "turn_on", {"entity_id": lights, "brightness_pct": 100, "transition": fade_s}, blocking=True
            )
            await asyncio.sleep(fade_s)
            self.phase = "lyser"; self._notify()
            if self.cfg.get(OPT_WAKE_PERSON):
                person = self._person()
                if person is not None:
                    await person.async_force_wake("vekkealarm")
            await asyncio.sleep(off_s)
            await self.hass.services.async_call("light", "turn_off", {"entity_id": lights}, blocking=True)
        except asyncio.CancelledError:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("%s: vekkesekvens feilet: %s", self.name, err)
        finally:
            self.running = False
            self.phase = "inaktiv"
            self._task = None
            self._notify()

"""Søvn-motor for én person (kind = person)."""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, time, timedelta
from statistics import fmean
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AWAY_ROOM_MIN,
    CONF_BED,
    CONF_BEDTIME_END,
    CONF_BEDTIME_START,
    CONF_DOOR,
    CONF_DOOR_CLOSED_MIN,
    CONF_ENABLED,
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
    CONF_DOOR_LATCH,
    CONF_LATCH_CONFIRM_MIN,
    CONF_PRIOR,
    CONF_SLEEP_SWITCH,
    CONF_THRESHOLD,
    CONF_WINDOW,
    ENTITY_KEYS,
    KIND_PERSON,
    PERSON_DEFAULTS as DEFAULTS,
    PROB,
)
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)


def _parse_time(value: str) -> time:
    parts = [int(p) for p in str(value).split(":")]
    while len(parts) < 3:
        parts.append(0)
    return time(parts[0], parts[1], parts[2])


def _in_window(now: datetime, start: str, end: str) -> bool:
    t = now.time()
    s, e = _parse_time(start), _parse_time(end)
    if s <= e:
        return s <= t < e
    return t >= s or t < e


def _bayes(prior: float, observations: list[tuple[bool | None, float, float]]) -> float:
    p = prior
    for observed, p_true, p_false in observations:
        if observed is None:
            continue
        if observed:
            num, den = p * p_true, p * p_true + (1 - p) * p_false
        else:
            num, den = p * (1 - p_true), p * (1 - p_true) + (1 - p) * (1 - p_false)
        p = num / den if den else p
    return p


class SovnCoordinator:
    """Beregner søvn-sannsynlighet og styrer bryteren for én person."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.cfg: dict[str, Any] = {**DEFAULTS, **entry.data, **entry.options}
        self.name: str = self.cfg[CONF_NAME]
        self.kind = KIND_PERSON
        self.prefix = slugify(f"{self.name} søvn")     # f.eks. sebastian_sovn
        self.last_change: datetime | None = None

        self.probability: float = 0.0
        self.sleeping: bool = False
        self.armed: bool = True            # må under terskel før ny "sover" etter tvungen vekking
        self.reason: str = "oppstart"
        self.observations: dict[str, bool | None] = {}

        self._pending_dir: bool | None = None
        self._pending_since: datetime | None = None
        self._last_presence_on: datetime | None = None
        # Dørlås: når døra lukkes mens noen nettopp var registrert i rommet, vet vi at personen
        # er der. Presence som faller ut etterpå betyr da bare at sensoren mistet personen –
        # låsen står til døra faktisk åpnes igjen.
        self._latch_since: datetime | None = None
        self._latch_before_open: bool = False
        self._i_rommet_kilde: str | None = None
        self._morning_door_opened: datetime | None = None
        self._hr_samples: deque[tuple[datetime, float]] = deque()

        self.self_update = False
        self._listeners: set[Callable[[], None]] = set()
        self._unsubs: list[Callable[[], None]] = []

    # ------------------------------------------------------------------ oppsett
    def _entity(self, key: str) -> str | None:
        return self.cfg.get(key) or None

    def _state(self, key: str) -> State | None:
        ent = self._entity(key)
        return self.hass.states.get(ent) if ent else None

    async def async_start(self) -> None:
        tracked = [e for e in (self._entity(k) for k in ENTITY_KEYS) if e]
        if tracked:
            self._unsubs.append(
                async_track_state_change_event(self.hass, tracked, self._on_state)
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_tick, timedelta(seconds=60))
        )

        now = dt_util.now()
        pres = self._state(CONF_PRESENCE)
        if pres and pres.state == "on":
            self._last_presence_on = now
        elif pres:
            self._last_presence_on = pres.last_changed
        # Etter omstart: står døra lukket og presence er på, er personen bekreftet inne.
        # Er presence av, vet vi ikke om hen gikk ut før omstarten – låsen settes da ikke.
        if pres and pres.state == "on" and self._door_closed_now():
            self._latch_since = now

        hr = self._state(CONF_HEART_RATE)
        if hr:
            self._push_hr(hr)

        sw = self._state(CONF_SLEEP_SWITCH)
        if sw:
            self.sleeping = sw.state == "on"

        await self._evaluate()

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @callback
    def async_add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(cb)
        return lambda: self._listeners.discard(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    # ------------------------------------------------------------------ hendelser
    def _push_hr(self, st: State | None) -> None:
        if not st or st.state in ("unknown", "unavailable", ""):
            return
        try:
            val = float(st.state)
        except ValueError:
            return
        self._hr_samples.append((st.last_updated, val))
        cutoff = dt_util.utcnow() - timedelta(minutes=self.cfg[CONF_HR_WINDOW_MIN])
        while self._hr_samples and self._hr_samples[0][0] < cutoff:
            self._hr_samples.popleft()

    async def _on_state(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        new: State | None = event.data.get("new_state")
        if new is None:
            return
        now = dt_util.now()

        if entity_id == self._entity(CONF_PRESENCE) and new.state == "on":
            self._last_presence_on = now
            # registrert i rommet med lukket dør → personen er inne, lås det fast
            if self._door_closed_now() and self._latch_since is None:
                self._latch_since = now

        elif entity_id == self._entity(CONF_HEART_RATE):
            self._push_hr(new)

        elif entity_id == self._entity(CONF_DOOR) and new.state == "off":
            # Døra lukket: var noen registrert i rommet like før, er personen inne nå.
            siden = self._last_presence_on
            pres = self._state(CONF_PRESENCE)
            fersk = pres is not None and pres.state == "on"
            if not fersk and siden is not None:
                fersk = (now - siden) <= timedelta(minutes=self.cfg[CONF_LATCH_CONFIRM_MIN])
            # Kort tur ut mens personen sov (do-tur): døra var åpen en liten stund, og hen var
            # bekreftet i rommet før den ble åpnet. Da regnes hen som tilbake i senga selv om
            # presence-sensoren ikke rekker å se det.
            kort_tur = False
            if not fersk and self._latch_before_open and self.sleeping:
                apen_siden = event.data.get("old_state")
                if apen_siden is not None:
                    kort_tur = (now - apen_siden.last_changed) < timedelta(
                        minutes=self.cfg[CONF_AWAY_ROOM_MIN]
                    )
            if fersk or kort_tur:
                self._latch_since = now
            self._latch_before_open = False

        elif entity_id == self._entity(CONF_DOOR) and new.state == "on":
            # Døra åpnet: nå kan personen gå ut, så låsen slippes og presence bestemmer igjen.
            self._latch_before_open = bool(self._latch_since)
            self._latch_since = None
            if _in_window(now, self.cfg[CONF_MORNING_FROM], self.cfg[CONF_MORNING_TO]):
                if self.cfg[CONF_NIGHT_DOOR_OK]:
                    self._morning_door_opened = now
                else:
                    await self._force_wake("dør åpnet om morgenen")

        elif entity_id == self._entity(CONF_HOME_SWITCH) and new.state == "off":
            await self._force_wake("forlot hjemmet")

        await self._evaluate()

    async def _on_tick(self, _now: datetime) -> None:
        await self._evaluate()

    # ------------------------------------------------------------------ logikk
    def _door_closed_now(self) -> bool:
        st = self._state(CONF_DOOR)
        return st is not None and st.state == "off"

    @property
    def latched(self) -> bool:
        """Er personen bekreftet i rommet av dørlåsen (presence + lukket dør, ingen døråpning etter)?"""
        return bool(self.cfg.get(CONF_DOOR_LATCH, True) and self._latch_since and self._door_closed_now())

    def _presence_in_room(self, now: datetime) -> bool | None:
        if self.latched:
            self._i_rommet_kilde = "dørlås"
            return True
        st = self._state(CONF_PRESENCE)
        if not st or st.state in ("unknown", "unavailable"):
            self._i_rommet_kilde = None
            return None
        if st.state == "on":
            self._i_rommet_kilde = "sensor"
            return True
        if self._last_presence_on is None:
            self._i_rommet_kilde = None
            return False
        innen = (now - self._last_presence_on) < timedelta(minutes=self.cfg[CONF_PRESENCE_HYST])
        self._i_rommet_kilde = "hysterese" if innen else None
        return innen

    def _presence_off_for(self, now: datetime) -> timedelta | None:
        """Hvor lenge presence har vært av – men bare hvis døra har vært åpnet i mellomtiden.

        Med dørlåsen aktiv betyr presence som faller ut med lukket dør at sensoren mistet
        personen, ikke at hen forlot rommet. Da returneres None, og «borte fra rommet»-regelen
        får ikke vekke noen som fortsatt ligger i senga."""
        if self.latched:
            return None
        st = self._state(CONF_PRESENCE)
        if not st or st.state != "off":
            return None
        siden = st.last_changed
        dor = self._state(CONF_DOOR)
        if self.cfg.get(CONF_DOOR_LATCH, True) and dor is not None and dor.state == "on":
            # døra står åpen: regn fra det seneste av «presence av» og «døra åpnet»
            siden = max(siden, dor.last_changed)
        return now - siden

    def _heart_rate(self, now: datetime) -> tuple[bool | None, bool | None, float | None]:
        """Returnerer (puls_lav, puls_hoy, glattet)."""
        st = self._state(CONF_HEART_RATE)
        if not st or st.state in ("unknown", "unavailable"):
            return None, None, None
        fresh = (now - st.last_updated) < timedelta(minutes=self.cfg[CONF_HR_FRESH_MIN])
        if not fresh:
            return None, None, None
        if self._hr_samples:
            smoothed = fmean(v for _, v in self._hr_samples)
        else:
            try:
                smoothed = float(st.state)
            except ValueError:
                return None, None, None
        try:
            current = float(st.state)
        except ValueError:
            current = smoothed
        return (
            smoothed < self.cfg[CONF_HR_SLEEP],
            current > self.cfg[CONF_HR_AWAKE],
            round(smoothed),
        )

    def _closed_for(self, key: str, minutes: int, now: datetime) -> bool | None:
        st = self._state(key)
        if not st or st.state in ("unknown", "unavailable"):
            return None
        return st.state == "off" and (now - st.last_changed) >= timedelta(minutes=minutes)

    def _bool_state(self, key: str) -> bool | None:
        st = self._state(key)
        if not st or st.state in ("unknown", "unavailable"):
            return None
        return st.state == "on"

    async def _evaluate(self) -> None:
        now = dt_util.now()
        cfg = self.cfg

        hjemme = self._bool_state(CONF_HOME_SWITCH)
        pres_st = self._state(CONF_PRESENCE)
        if pres_st is not None and pres_st.state == "on" and self._door_closed_now() and self._latch_since is None:
            self._latch_since = now
        if not self._door_closed_now():
            self._latch_since = None
        if hjemme is False:
            self._latch_since = None      # borte fra huset → ingen lås å holde
            self._latch_before_open = False
        sovevindu = _in_window(now, cfg[CONF_BEDTIME_START], cfg[CONF_BEDTIME_END])
        i_rommet = self._presence_in_room(now)
        # Når døra kan åpnes om natta teller den som lukket med en gang den lukkes,
        # slik at do-turer ikke drar sannsynligheten ned i lang tid etterpå.
        dor_lukket = self._closed_for(
            CONF_DOOR, 0 if cfg[CONF_NIGHT_DOOR_OK] else cfg[CONF_DOOR_CLOSED_MIN], now
        )
        vindu_apent = self._bool_state(CONF_WINDOW)
        puls_lav, puls_hoy, puls_glattet = self._heart_rate(now)
        i_senga = self._bool_state(CONF_BED)

        door_key = "dor_lukket_natt_ok" if cfg[CONF_NIGHT_DOOR_OK] else "dor_lukket"
        obs = [
            (hjemme, *PROB["hjemme"]),
            (sovevindu, *PROB["sovevindu"]),
            (i_rommet, *PROB["i_rommet_laast" if self.latched else "i_rommet"]),
            (dor_lukket, *PROB[door_key]),
            (vindu_apent, *PROB["vindu_apent"]),
            (puls_lav, *PROB["puls_lav"]),
            (puls_hoy, *PROB["puls_hoy"]),
            (i_senga, *PROB["i_senga"]),
        ]
        self.probability = _bayes(cfg[CONF_PRIOR], obs)
        self.observations = {
            "hjemme": hjemme,
            "sovevindu": sovevindu,
            "i_rommet": i_rommet,
            "dør_lukket": dor_lukket,
            "vindu_åpent": vindu_apent,
            "puls_lav": puls_lav,
            "puls_høy": puls_hoy,
            "puls_glattet": puls_glattet,
            "i_senga": i_senga,
        }
        self.observations["i_rommet_kilde"] = self._i_rommet_kilde
        self.observations["dorlas"] = self.latched or None

        # --- Tvungne vekkeregler ---
        if self.sleeping:
            if hjemme is False:
                await self._force_wake("forlot hjemmet")
            off_for = self._presence_off_for(now)
            if off_for is not None and off_for >= timedelta(minutes=cfg[CONF_AWAY_ROOM_MIN]):
                await self._force_wake(f"borte fra rommet {cfg[CONF_AWAY_ROOM_MIN]} min")
            if (
                self._morning_door_opened
                and off_for is not None
                and off_for >= timedelta(minutes=cfg[CONF_MORNING_AWAY_MIN])
            ):
                await self._force_wake("gikk ut om morgenen")
        if self._morning_door_opened and not _in_window(
            now, cfg[CONF_MORNING_FROM], cfg[CONF_MORNING_TO]
        ):
            self._morning_door_opened = None

        # --- Terskel med forsinkelse ---
        above = self.probability >= cfg[CONF_THRESHOLD]
        if not above:
            self.armed = True

        if above and not self.sleeping and self.armed:
            self._advance_pending(True, now, cfg[CONF_ON_DELAY], "sannsynlighet over terskel")
        elif not above and self.sleeping:
            self._advance_pending(False, now, cfg[CONF_OFF_DELAY], "sannsynlighet under terskel")
        else:
            self._pending_dir = self._pending_since = None

        await self._write_switch()
        self._notify()

    def _advance_pending(self, direction: bool, now: datetime, delay_min: int, reason: str) -> None:
        if self._pending_dir != direction:
            self._pending_dir, self._pending_since = direction, now
            return
        if now - self._pending_since >= timedelta(minutes=delay_min):
            self.sleeping = direction
            self.reason = reason
            self.last_change = now
            self._pending_dir = self._pending_since = None
            if direction:
                self._morning_door_opened = None

    async def _force_wake(self, reason: str) -> None:
        if not self.sleeping and self.armed is False:
            return
        if self.sleeping:
            self.last_change = dt_util.now()
        self.sleeping = False
        self.armed = False
        self.reason = reason
        self._pending_dir = self._pending_since = None
        self._morning_door_opened = None
        _LOGGER.debug("%s vekket: %s", self.name, reason)

    async def async_force_wake(self, reason: str) -> None:
        """Tvungen vekking utenfra (f.eks. vekkealarmen)."""
        await self._force_wake(reason)
        await self._evaluate()

    async def async_set_sleeping(self, sleeping: bool, reason: str = "manuelt") -> None:
        """Manuell overstyring fra kort/tjeneste. Skriver til bryteren med en gang."""
        if sleeping:
            self.armed = True
            self.sleeping = True
        else:
            self.sleeping = False
            self.armed = False
        self.reason = reason
        self.last_change = dt_util.now()
        self._pending_dir = self._pending_since = None
        await self._write_switch()
        self._notify()

    async def async_set_setting(self, key: str, value: Any) -> None:
        """Endre en innstilling fra en entitet; lagres i options uten reload."""
        self.cfg[key] = value
        self.self_update = True
        self.hass.config_entries.async_update_entry(
            self.entry, options={**self.entry.options, key: value}
        )
        await self._evaluate()

    async def _write_switch(self) -> None:
        ent = self._entity(CONF_SLEEP_SWITCH)
        if not ent or not self.cfg.get(CONF_ENABLED, True):
            return
        st = self.hass.states.get(ent)
        desired = "on" if self.sleeping else "off"
        if st and st.state == desired:
            return
        await self.hass.services.async_call(
            "switch", f"turn_{desired}", {"entity_id": ent}, blocking=False
        )

    @property
    def pending(self) -> str | None:
        if self._pending_dir is None:
            return None
        return "sovner" if self._pending_dir else "våkner"

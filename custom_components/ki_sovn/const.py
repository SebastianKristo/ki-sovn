"""Konstanter for KI Søvn & Vekking."""

DOMAIN = "ki_sovn"

# Type oppføring (entry.data["kind"]). Mangler nøkkelen (v1) = person.
CONF_KIND = "kind"
KIND_PERSON = "person"
KIND_VEKKING = "vekking"

CONF_NAME = "name"

# ======================================================= Person (søvndeteksjon)
CONF_HOME_SWITCH = "home_switch"        # on = hjemme
CONF_SLEEP_SWITCH = "sleep_switch"      # skrives til (Homey), on = sover
CONF_PRESENCE = "presence_sensor"       # binary_sensor, on = person i rommet
CONF_DOOR = "door_sensor"               # binary_sensor, on = åpen
CONF_WINDOW = "window_sensor"           # binary_sensor, on = åpen
CONF_HEART_RATE = "heart_rate_sensor"   # sensor, bpm
CONF_BED = "bed_sensor"                 # binary_sensor, on = i senga

ENTITY_KEYS = (CONF_HOME_SWITCH, CONF_PRESENCE, CONF_DOOR, CONF_WINDOW, CONF_HEART_RATE, CONF_BED)

CONF_BEDTIME_START = "bedtime_start"
CONF_BEDTIME_END = "bedtime_end"
CONF_MORNING_FROM = "morning_from"
CONF_MORNING_TO = "morning_to"
CONF_NIGHT_DOOR_OK = "night_door_ok"
CONF_ENABLED = "enabled"

CONF_THRESHOLD = "threshold"
CONF_PRIOR = "prior"
CONF_ON_DELAY = "on_delay_min"
CONF_OFF_DELAY = "off_delay_min"
CONF_PRESENCE_HYST = "presence_hyst_min"
CONF_AWAY_ROOM_MIN = "away_room_min"
CONF_MORNING_AWAY_MIN = "morning_away_min"
CONF_DOOR_CLOSED_MIN = "door_closed_min"
CONF_HR_SLEEP = "hr_sleep_bpm"
CONF_HR_AWAKE = "hr_awake_bpm"
CONF_HR_FRESH_MIN = "hr_fresh_min"
CONF_HR_WINDOW_MIN = "hr_window_min"
CONF_DOOR_LATCH = "door_latch"            # presence som faller ut = fortsatt i rommet, helt til døra åpnes
CONF_LATCH_CONFIRM_MIN = "latch_confirm_min"   # presence må vært på innen så mange min før døra lukkes

PERSON_DEFAULTS = {
    CONF_BEDTIME_START: "22:00",
    CONF_BEDTIME_END: "10:00",
    CONF_MORNING_FROM: "05:00",
    CONF_MORNING_TO: "12:00",
    CONF_NIGHT_DOOR_OK: False,
    CONF_ENABLED: True,
    CONF_THRESHOLD: 0.8,
    CONF_PRIOR: 0.25,
    CONF_ON_DELAY: 10,
    CONF_OFF_DELAY: 10,
    CONF_PRESENCE_HYST: 30,
    CONF_AWAY_ROOM_MIN: 30,
    CONF_MORNING_AWAY_MIN: 5,
    CONF_DOOR_CLOSED_MIN: 20,
    CONF_HR_SLEEP: 54,
    CONF_HR_AWAKE: 65,
    CONF_HR_FRESH_MIN: 60,
    CONF_HR_WINDOW_MIN: 20,
    CONF_DOOR_LATCH: True,
    CONF_LATCH_CONFIRM_MIN: 10,
}

# (P(obs|sover), P(obs|våken))
PROB = {
    "hjemme": (0.99, 0.55),
    "sovevindu": (0.95, 0.35),
    "i_rommet": (0.96, 0.30),
    "i_rommet_laast": (0.98, 0.22),   # bekreftet av dørlåsen: sterkere enn en rå presence-treff
    "dor_lukket": (0.90, 0.25),
    "dor_lukket_natt_ok": (0.80, 0.40),
    "vindu_apent": (0.15, 0.30),
    "puls_lav": (0.85, 0.15),
    "puls_hoy": (0.05, 0.50),
    "i_senga": (0.95, 0.10),
}

# key: (translation_key, min, max, step, unit, scale)  lagret = vist * scale
PERSON_NUMBERS = {
    CONF_THRESHOLD: ("terskel", 50, 99, 1, "%", 0.01),
    CONF_ON_DELAY: ("forsinkelse_sovner", 0, 60, 1, "min", 1),
    CONF_OFF_DELAY: ("forsinkelse_vaakner", 0, 60, 1, "min", 1),
    CONF_PRESENCE_HYST: ("hold_i_rommet", 0, 120, 5, "min", 1),
    CONF_AWAY_ROOM_MIN: ("borte_fra_rommet", 5, 180, 5, "min", 1),
    CONF_DOOR_CLOSED_MIN: ("dor_lukket_min", 0, 120, 5, "min", 1),
    CONF_LATCH_CONFIRM_MIN: ("dorlas_bekreft", 1, 60, 1, "min", 1),
    CONF_HR_SLEEP: ("puls_sover", 30, 100, 1, "bpm", 1),
    CONF_HR_AWAKE: ("puls_vaaken", 40, 150, 1, "bpm", 1),
}
PERSON_TIMES = {
    CONF_BEDTIME_START: "sovevindu_start",
    CONF_BEDTIME_END: "sovevindu_slutt",
    CONF_MORNING_FROM: "morgen_fra",
}
PERSON_SWITCHES = {
    CONF_ENABLED: "automatisk",
    CONF_NIGHT_DOOR_OK: "dor_om_natta_ok",
    CONF_DOOR_LATCH: "dorlas",
}

# ======================================================= Vekking (vekkealarm)
CONF_LIGHTS = "lights"
CONF_NIGHT_LIGHT = "night_light"
CONF_CONDITIONS = "conditions"
CONF_START_PCT = "start_pct"
CONF_PERSON = "person"            # binary_sensor.<navn>_sovn_sover fra en person-oppføring (valgfri)

DAYS = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lordag", "sondag"]
DAY_NAMES = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]

OPT_MASTER = "master"
OPT_NIGHT_LIGHT_ON = "nattlampe"
OPT_FADE = "fade_minutter"
OPT_OFF_AFTER = "av_etter_minutter"
OPT_WAKE_PERSON = "vekk_person"          # marker personen som våken når fade er ferdig
OPT_ONLY_IF_ASLEEP = "bare_hvis_sover"   # hopp over alarmen hvis personen er våken


def opt_time(day: str) -> str:
    return f"{day}_tid"


def opt_active(day: str) -> str:
    return f"{day}_aktiv"


VEKKING_DEFAULTS = {
    OPT_MASTER: True,
    OPT_NIGHT_LIGHT_ON: False,
    OPT_FADE: 10,
    OPT_OFF_AFTER: 30,
    OPT_WAKE_PERSON: True,
    OPT_ONLY_IF_ASLEEP: False,
    CONF_START_PCT: 1,
    **{opt_time(d): "07:00" for d in DAYS},
    **{opt_active(d): d not in ("lordag", "sondag") for d in DAYS},
}

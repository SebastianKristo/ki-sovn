"""Konstanter for KI Søvn."""

DOMAIN = "ki_sovn"

# --- Person og entiteter ---
CONF_NAME = "name"
CONF_HOME_SWITCH = "home_switch"        # on = hjemme
CONF_SLEEP_SWITCH = "sleep_switch"      # skrives til (Homey), on = sover
CONF_PRESENCE = "presence_sensor"       # binary_sensor, on = person i rommet
CONF_DOOR = "door_sensor"               # binary_sensor, on = åpen
CONF_WINDOW = "window_sensor"           # binary_sensor, on = åpen
CONF_HEART_RATE = "heart_rate_sensor"   # sensor, bpm
CONF_BED = "bed_sensor"                 # binary_sensor, on = i senga

ENTITY_KEYS = (
    CONF_HOME_SWITCH,
    CONF_PRESENCE,
    CONF_DOOR,
    CONF_WINDOW,
    CONF_HEART_RATE,
    CONF_BED,
)

# --- Tider ---
CONF_BEDTIME_START = "bedtime_start"    # "HH:MM"
CONF_BEDTIME_END = "bedtime_end"
CONF_MORNING_FROM = "morning_from"      # dør åpnes etter dette = våken
CONF_MORNING_TO = "morning_to"
CONF_NIGHT_DOOR_OK = "night_door_ok"    # True: døra kan åpnes om natta (do) uten å vekke

# --- Terskler ---
CONF_THRESHOLD = "threshold"            # 0–1
CONF_PRIOR = "prior"
CONF_ON_DELAY = "on_delay_min"
CONF_OFF_DELAY = "off_delay_min"
CONF_PRESENCE_HYST = "presence_hyst_min"      # "i rommet" holder seg så lenge
CONF_AWAY_ROOM_MIN = "away_room_min"          # borte fra rommet så lenge = våken
CONF_MORNING_AWAY_MIN = "morning_away_min"    # etter morgen-døråpning: borte så lenge = våken
CONF_DOOR_CLOSED_MIN = "door_closed_min"
CONF_HR_SLEEP = "hr_sleep_bpm"
CONF_HR_AWAKE = "hr_awake_bpm"
CONF_HR_FRESH_MIN = "hr_fresh_min"
CONF_HR_WINDOW_MIN = "hr_window_min"

DEFAULTS = {
    CONF_BEDTIME_START: "22:00",
    CONF_BEDTIME_END: "10:00",
    CONF_MORNING_FROM: "05:00",
    CONF_MORNING_TO: "12:00",
    CONF_NIGHT_DOOR_OK: False,
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
}

# Sannsynligheter (P(obs|sover), P(obs|våken))
PROB = {
    "hjemme": (0.99, 0.55),
    "sovevindu": (0.95, 0.35),
    "i_rommet": (0.96, 0.30),
    "dor_lukket": (0.90, 0.25),
    "dor_lukket_natt_ok": (0.80, 0.40),   # lavere vekt når døra kan åpnes om natta
    "vindu_apent": (0.15, 0.30),
    "puls_lav": (0.85, 0.15),
    "puls_hoy": (0.05, 0.50),
    "i_senga": (0.95, 0.10),
}

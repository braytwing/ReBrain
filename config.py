# =============================================================
#  STROOP COGNITIVO v2 — CONFIGURACIÓN GENERAL
# =============================================================

LANGUAGE = "es"   # "es" | "en"

PATIENT_ID  = "PAC001"
PATIENT_AGE = 30

COLORS = {
    "es": {
        "ROJO":     (220, 50,  50),
        "AZUL":     (50,  100, 220),
        "VERDE":    (50,  180, 80),
        "AMARILLO": (220, 200, 30),
    },
    "en": {
        "RED":    (220, 50,  50),
        "BLUE":   (50,  100, 220),
        "GREEN":  (50,  180, 80),
        "YELLOW": (220, 200, 30),
    },
}

# ══════════════════════════════════════════════════════════════
#  GRUPOS DE EDAD Y PARÁMETROS NORMATIVOS
#  Ref: Golden (1978), Troyer et al. (2006), Mitrushina et al. (2005)
# ══════════════════════════════════════════════════════════════
AGE_GROUPS = {
    "child": {
        "label":                 {"es": "Niño/a (8–12)",        "en": "Child (8–12)"},
        "range":                 (8, 12),
        "norm_rt_congruent":     1400,
        "norm_rt_incongruent":   2000,
        "norm_interference":      600,
        "norm_accuracy":           82,
        "levels": {
            1: {"time_limit": 120.0, "trials": 8,  "target_size": 0.40, "incongruent": False},
            2: {"time_limit": 120.0, "trials": 10, "target_size": 0.40, "incongruent": True},
            3: {"time_limit": 90.0, "trials": 14, "target_size": 0.30, "incongruent": True},
            4: {"time_limit": 90.0, "trials": 16, "target_size": 0.25, "incongruent": True},
            5: {"time_limit": 60.5, "trials": 20, "target_size": 0.25, "incongruent": True},
        },
    },
    "young_adult": {
        "label":                 {"es": "Adulto joven (18–35)", "en": "Young adult (18–35)"},
        "range":                 (18, 35),
        "norm_rt_congruent":      900,
        "norm_rt_incongruent":   1250,
        "norm_interference":      350,
        "norm_accuracy":           90,
        "levels": {
            1: {"time_limit": 120.0, "trials": 8,  "target_size": 0.40, "incongruent": False},
            2: {"time_limit": 120.0, "trials": 10, "target_size": 0.40, "incongruent": True},
            3: {"time_limit": 90.0, "trials": 14, "target_size": 0.30, "incongruent": True},
            4: {"time_limit": 90.0, "trials": 16, "target_size": 0.25, "incongruent": True},
            5: {"time_limit": 60.5, "trials": 20, "target_size": 0.25, "incongruent": True},
        },
    },
    "middle_adult": {
        "label":                 {"es": "Adulto medio (36–59)", "en": "Middle adult (36–59)"},
        "range":                 (36, 59),
        "norm_rt_congruent":     1050,
        "norm_rt_incongruent":   1500,
        "norm_interference":      450,
        "norm_accuracy":           87,
        "levels": {
            1: {"time_limit": 120.0, "trials": 8,  "target_size": 0.40, "incongruent": False},
            2: {"time_limit": 120.0, "trials": 10, "target_size": 0.40, "incongruent": True},
            3: {"time_limit": 90.0, "trials": 14, "target_size": 0.30, "incongruent": True},
            4: {"time_limit": 90.0, "trials": 16, "target_size": 0.25, "incongruent": True},
            5: {"time_limit": 60.5, "trials": 20, "target_size": 0.25, "incongruent": True},
        },
    },
    "older_adult": {
        "label":                 {"es": "Adulto mayor (60+)",   "en": "Older adult (60+)"},
        "range":                 (60, 120),
        "norm_rt_congruent":     1300,
        "norm_rt_incongruent":   1950,
        "norm_interference":      650,
        "norm_accuracy":           80,
        "levels": {
            1: {"time_limit": 120.0, "trials": 8,  "target_size": 0.45, "incongruent": False},
            2: {"time_limit": 120.0, "trials": 10, "target_size": 0.45, "incongruent": True},
            3: {"time_limit": 90.0, "trials": 14, "target_size": 0.30, "incongruent": True},
            4: {"time_limit": 90.0, "trials": 16, "target_size": 0.25, "incongruent": True},
            5: {"time_limit": 60.5, "trials": 20, "target_size": 0.25, "incongruent": True},
        },
    },
}

LEVEL_NAMES = {
    "es": {1: "Calentamiento", 2: "Básico", 3: "Intermedio", 4: "Avanzado", 5: "Experto"},
    "en": {1: "Warm-up",       2: "Basic",  3: "Intermediate",4: "Advanced", 5: "Expert"},
}

LEVEL_DESCRIPTIONS = {
    "es": {
        1: "Colores congruentes — sin interferencia",
        2: "Incongruente — palabra ≠ color",
        3: "Incongruente + tiempo reducido",
        4: "Incongruente + zonas pequeñas",
        5: "Máxima interferencia",
    },
    "en": {
        1: "Congruent colors — no interference",
        2: "Incongruent — word ≠ color",
        3: "Incongruent + reduced time",
        4: "Incongruent + small zones",
        5: "Maximum interference",
    },
}

# ── Cámara ────────────────────────────────────────────────────
CAMERA_INDEX       = 0
FINGER_SMOOTHING   = 7
MIN_DETECTION_CONF = 0.55
MIN_TRACKING_CONF  = 0.55
DWELL_TIME_MS      = 450

# ── Pantalla ──────────────────────────────────────────────────
FULLSCREEN          = True
FONT_WORD_SIZE_FRAC = 0.05
FONT_LABEL_SIZE_FRAC= 0.030
BG_COLOR            = (12, 12, 22)
TIMER_BAR_HEIGHT    = 12
CAM_FEED_W_FRAC     = 0.54
CAM_FEED_H_FRAC     = 0.64

# ── Datos ─────────────────────────────────────────────────────
DATA_DIR    = "data"
REPORTS_DIR = "reports"


# ── Helpers ───────────────────────────────────────────────────
def get_age_group(age: int) -> str:
    for key, grp in AGE_GROUPS.items():
        lo, hi = grp["range"]
        if lo <= age <= hi:
            return key
    return "child" if age < 8 else "older_adult"


def get_level_config(age_group: str, level: int) -> dict:
    return AGE_GROUPS[age_group]["levels"][level]

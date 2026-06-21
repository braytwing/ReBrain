"""
data_recorder.py  v2
─────────────────────
Igual que v1 + columnas de grupo de edad y comparación normativa.
"""

import csv
import os
from datetime import datetime
from config import DATA_DIR, PATIENT_ID, AGE_GROUPS

FIELDNAMES = [
    "patient_id", "age_group", "session_date", "session_time", "trial_number",
    "level", "word", "word_color", "word_color_rgb",
    "correct_answer", "congruent",
    "response", "correct", "timed_out",
    "rt_ms", "decision_onset_ms", "movement_time_ms",
    "peak_speed", "path_length", "motor_corrections", "tremor_index",
    "n_trajectory_points", "time_limit_s",
    # Comparación normativa
    "norm_rt_ref", "rt_vs_norm_pct",
]


class DataRecorder:

    def __init__(self, patient_id: str = PATIENT_ID, age_group: str = "young_adult"):
        self.patient_id   = patient_id
        self.age_group    = age_group
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.session_time = datetime.now().strftime("%H-%M-%S")
        self.trials       = []
        self._trial_count = 0

        os.makedirs(DATA_DIR, exist_ok=True)
        fname = f"{patient_id}_{self.session_date}_{self.session_time}.csv"
        self.filepath = os.path.join(DATA_DIR, fname)

        with open(self.filepath, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()

    def record_trial(self, level, word, word_color, word_color_rgb,
                     correct_answer, congruent, response, rt_ms,
                     decision_onset_ms, timed_out, motor_metrics, time_limit_s):

        self._trial_count += 1
        correct = (response == correct_answer) and not timed_out
        movement_time_ms = (rt_ms - decision_onset_ms) if decision_onset_ms else rt_ms

        # Referencia normativa
        grp = AGE_GROUPS.get(self.age_group, {})
        norm_rt_ref = (grp.get("norm_rt_congruent", 0) if congruent
                       else grp.get("norm_rt_incongruent", 0))
        rt_vs_norm  = round((rt_ms / norm_rt_ref - 1) * 100, 1) if norm_rt_ref else ""

        row = {
            "patient_id":          self.patient_id,
            "age_group":           self.age_group,
            "session_date":        self.session_date,
            "session_time":        self.session_time,
            "trial_number":        self._trial_count,
            "level":               level,
            "word":                word,
            "word_color":          word_color,
            "word_color_rgb":      str(word_color_rgb),
            "correct_answer":      correct_answer,
            "congruent":           congruent,
            "response":            response or "TIMEOUT",
            "correct":             correct,
            "timed_out":           timed_out,
            "rt_ms":               round(rt_ms, 2),
            "decision_onset_ms":   round(decision_onset_ms, 2) if decision_onset_ms else "",
            "movement_time_ms":    round(movement_time_ms, 2),
            "peak_speed":          motor_metrics.get("peak_speed", ""),
            "path_length":         motor_metrics.get("path_length", ""),
            "motor_corrections":   motor_metrics.get("corrections", ""),
            "tremor_index":        motor_metrics.get("tremor_index", ""),
            "n_trajectory_points": motor_metrics.get("n_points", ""),
            "time_limit_s":        time_limit_s,
            "norm_rt_ref":         norm_rt_ref,
            "rt_vs_norm_pct":      rt_vs_norm,
        }

        self.trials.append(row)
        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)

        return correct

    def get_summary(self):
        if not self.trials:
            return {}
        summary = {}
        for lvl in sorted(set(t["level"] for t in self.trials)):
            lt  = [t for t in self.trials if t["level"] == lvl]
            ok  = [t for t in lt if t["correct"]]
            rts = [t["rt_ms"] for t in lt if not t["timed_out"]]
            c_rts = [t["rt_ms"] for t in self.trials
                     if t["level"] == 1 and not t["timed_out"]]
            mean_c = sum(c_rts) / len(c_rts) if c_rts else 0
            mean_r = sum(rts) / len(rts) if rts else 0

            tremors = [t["tremor_index"] for t in lt
                       if t["tremor_index"] not in ("", None)]
            corrs   = [t["motor_corrections"] for t in lt
                       if t["motor_corrections"] not in ("", None)]

            summary[lvl] = {
                "total":            len(lt),
                "correct":          len(ok),
                "accuracy_pct":     round(len(ok) / max(len(lt), 1) * 100, 1),
                "mean_rt_ms":       round(mean_r, 1),
                "min_rt_ms":        round(min(rts), 1) if rts else 0,
                "max_rt_ms":        round(max(rts), 1) if rts else 0,
                "std_rt_ms":        round(
                    (sum((r - mean_r)**2 for r in rts) / max(len(rts),1)) ** 0.5, 1),
                "timeouts":         sum(1 for t in lt if t["timed_out"]),
                "interference_ms":  round(mean_r - mean_c, 1),
                "mean_tremor":      round(sum(tremors)/max(len(tremors),1), 4),
                "mean_corrections": round(sum(corrs)/max(len(corrs),1), 2),
            }
        return summary

    def get_all_trials(self):
        return self.trials

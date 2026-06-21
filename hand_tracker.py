"""
hand_tracker.py  v2
────────────────────
- Calibración de zona de movimiento del paciente
- Normalización de coordenadas al espacio calibrado
- Manejo seguro de mano fuera de frame (sin excepciones)
- Métricas motoras completas
"""

import time
import math
import collections
import cv2
import mediapipe as mp
from config import (CAMERA_INDEX, FINGER_SMOOTHING,
                    MIN_DETECTION_CONF, MIN_TRACKING_CONF,
                    DWELL_TIME_MS)


# ══════════════════════════════════════════════════════════════
#  MÉTRICAS MOTORAS
# ══════════════════════════════════════════════════════════════

class MotorMetrics:
    def __init__(self):
        self.trajectory  = []
        self.peak_speed  = 0.0
        self.path_length = 0.0
        self.corrections = 0
        self._prev_angle = None

    def reset(self):
        self.trajectory  = []
        self.peak_speed  = 0.0
        self.path_length = 0.0
        self.corrections = 0
        self._prev_angle = None

    def update(self, x, y):
        t = time.perf_counter()
        self.trajectory.append((x, y, t))
        if len(self.trajectory) >= 2:
            x0, y0, t0 = self.trajectory[-2]
            dt = t - t0
            if dt > 0:
                dx, dy = x - x0, y - y0
                speed = math.hypot(dx, dy) / dt
                self.peak_speed   = max(self.peak_speed, speed)
                self.path_length += math.hypot(dx, dy)
                angle = math.atan2(dy, dx)
                if self._prev_angle is not None:
                    diff = abs(angle - self._prev_angle)
                    if diff > math.pi:
                        diff = 2 * math.pi - diff
                    if diff > math.pi / 2:
                        self.corrections += 1
                self._prev_angle = angle

    def tremor_index(self):
        if len(self.trajectory) < 4:
            return 0.0
        speeds = []
        for i in range(1, len(self.trajectory)):
            x0, y0, t0 = self.trajectory[i - 1]
            x1, y1, t1 = self.trajectory[i]
            dt = t1 - t0
            if dt > 0:
                speeds.append(math.hypot(x1 - x0, y1 - y0) / dt)
        if not speeds:
            return 0.0
        mean = sum(speeds) / len(speeds)
        var  = sum((s - mean) ** 2 for s in speeds) / len(speeds)
        return math.sqrt(var)

    def to_dict(self):
        return {
            "peak_speed":   round(self.peak_speed,   4),
            "path_length":  round(self.path_length,  4),
            "corrections":  self.corrections,
            "tremor_index": round(self.tremor_index(), 4),
            "n_points":     len(self.trajectory),
        }


# ══════════════════════════════════════════════════════════════
#  CALIBRACIÓN
# ══════════════════════════════════════════════════════════════

class CalibrationData:
    """
    Almacena el bounding box del espacio de movimiento del paciente.
    Las coordenadas son fracciones normalizadas (0-1) del frame de cámara.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.min_x   = 1.0
        self.max_x   = 0.0
        self.min_y   = 1.0
        self.max_y   = 0.0
        self.n_samples = 0
        self.valid   = False

    def update(self, x, y):
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)
        self.n_samples += 1

    def finalize(self, margin: float = 0.08):
        """Expande el bounding box con un margen y marca como válida."""
        span_x = self.max_x - self.min_x
        span_y = self.max_y - self.min_y
        # Requiere movimiento mínimo para ser válida
        if span_x < 0.05 or span_y < 0.05:
            return False
        self.min_x = max(0.0, self.min_x - margin)
        self.max_x = min(1.0, self.max_x + margin)
        self.min_y = max(0.0, self.min_y - margin)
        self.max_y = min(1.0, self.max_y + margin)
        self.valid = True
        return True

    def normalize(self, x, y):
        """
        Mapea coordenadas crudas (0-1) al espacio calibrado (0-1).
        Si la calibración no es válida, devuelve coords originales.
        """
        if not self.valid:
            return x, y
        span_x = self.max_x - self.min_x
        span_y = self.max_y - self.min_y
        if span_x == 0 or span_y == 0:
            return x, y
        nx = (x - self.min_x) / span_x
        ny = (y - self.min_y) / span_y
        return max(0.0, min(1.0, nx)), max(0.0, min(1.0, ny))


# ══════════════════════════════════════════════════════════════
#  HAND TRACKER
# ══════════════════════════════════════════════════════════════

class HandTracker:

    def __init__(self):
        self._mp_hands = mp.solutions.hands
        self._hands    = self._mp_hands.Hands(
            max_num_hands            = 1,
            min_detection_confidence = MIN_DETECTION_CONF,
            min_tracking_confidence  = MIN_TRACKING_CONF,
        )
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS,           30)

        self._smooth_x = collections.deque(maxlen=FINGER_SMOOTHING)
        self._smooth_y = collections.deque(maxlen=FINGER_SMOOTHING)

        self._dwell_zone  = None
        self._dwell_start = None

        self.metrics     = MotorMetrics()
        self.calibration = CalibrationData()
        self._active     = False

        # Último frame válido (evita crash si cámara falla un frame)
        self._last_frame = None

    # ── Cámara ────────────────────────────────────────────────

    def is_opened(self) -> bool:
        return self._cap.isOpened()

    def get_frame_and_finger(self):
        """
        Retorna (frame_bgr, fx_norm, fy_norm).
        fx/fy son coordenadas normalizadas [0-1] ya calibradas.
        Si la mano no está visible devuelve fx=fy=None sin excepciones.
        """
        ret, frame = self._cap.read()
        if not ret or frame is None:
            # Devolver último frame válido para no cortar el video
            frame = self._last_frame
            if frame is None:
                return None, None, None
        else:
            frame = cv2.flip(frame, 1)
            self._last_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            res = self._hands.process(rgb)
        except Exception:
            return frame, None, None

        fx, fy = None, None

        if res and res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            raw_x = lm[8].x   # punta índice
            raw_y = lm[8].y

            # Suavizado temporal
            self._smooth_x.append(raw_x)
            self._smooth_y.append(raw_y)
            raw_x = sum(self._smooth_x) / len(self._smooth_x)
            raw_y = sum(self._smooth_y) / len(self._smooth_y)

            # Aplicar calibración
            fx, fy = self.calibration.normalize(raw_x, raw_y)

            if self._active:
                self.metrics.update(fx, fy)

            # Dibujar skeleton sobre el frame
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                res.multi_hand_landmarks[0],
                self._mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style(),
            )

        return frame, fx, fy

    # ── Dwell detection ───────────────────────────────────────

    def check_dwell_px(self, fx_px, fy_px, zones: dict):
        """
        zones: {nombre: pygame.Rect}
        Retorna (zone_name | None, progress 0-1)
        """
        if fx_px is None or fy_px is None:
            self._dwell_zone  = None
            self._dwell_start = None
            return None, 0.0

        hit_zone = None
        for name, rect in zones.items():
            if rect.collidepoint(fx_px, fy_px):
                hit_zone = name
                break

        if hit_zone != self._dwell_zone:
            self._dwell_zone  = hit_zone
            self._dwell_start = time.perf_counter() if hit_zone else None

        progress = 0.0
        if self._dwell_zone and self._dwell_start:
            elapsed_ms = (time.perf_counter() - self._dwell_start) * 1000
            progress   = min(elapsed_ms / DWELL_TIME_MS, 1.0)
            if elapsed_ms >= DWELL_TIME_MS:
                chosen = self._dwell_zone
                self._dwell_zone  = None
                self._dwell_start = None
                return chosen, 1.0

        return None, progress

    # ── Calibración ───────────────────────────────────────────

    def start_calibration(self):
        self.calibration.reset()

    def update_calibration(self, frame):
        """
        Procesa un frame durante la fase de calibración.
        Retorna (frame_con_skeleton, fx_raw, fy_raw) — sin normalizar.
        """
        if frame is None:
            return None, None, None
        rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        try:
            res = self._hands.process(rgb)
        except Exception:
            return cv2.flip(frame, 1), None, None

        frame_out = cv2.flip(frame, 1)
        fx, fy = None, None
        if res and res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            fx, fy = lm[8].x, lm[8].y
            self.calibration.update(fx, fy)
            mp.solutions.drawing_utils.draw_landmarks(
                frame_out,
                res.multi_hand_landmarks[0],
                self._mp_hands.HAND_CONNECTIONS,
            )
        return frame_out, fx, fy

    def finalize_calibration(self) -> bool:
        return self.calibration.finalize(margin=0.08)

    # ── Control de ensayo ─────────────────────────────────────

    def start_trial(self):
        self.metrics.reset()
        self._dwell_zone  = None
        self._dwell_start = None
        self._active      = True

    def end_trial(self) -> dict:
        self._active = False
        return self.metrics.to_dict()

    def release(self):
        try:
            self._cap.release()
            self._hands.close()
        except Exception:
            pass

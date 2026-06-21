"""
main.py  v2.2 — Edición Mission Brain Hackathon (Final)
────────────
Novedades:
  - Fondo estático unificado en todas las pantallas
  - Sistema de UI dinámico (Cajas de colisión infalibles)
  - Fase de introducción rediseñada ("La búsqueda del vaquero")
  - Feedback narrativo: El vaquero alienta al jugador tras cada intento.
  - Integración de audio (Fayenza) con rutas dinámicas relativas.
"""

import sys, os, random, time, math
import cv2, pygame
import numpy as np

from config import (COLORS, AGE_GROUPS, LEVEL_NAMES, LEVEL_DESCRIPTIONS,
                    LANGUAGE, FULLSCREEN, FONT_WORD_SIZE_FRAC,
                    FONT_LABEL_SIZE_FRAC, BG_COLOR, TIMER_BAR_HEIGHT,
                    CAM_FEED_W_FRAC, CAM_FEED_H_FRAC, DWELL_TIME_MS,
                    DATA_DIR, REPORTS_DIR, get_age_group, get_level_config)
from hand_tracker   import HandTracker
from data_recorder  import DataRecorder
from report_generator import generate_full_report

# ── Constantes globales ───────────────────────────────────────
LANG         = LANGUAGE
COLOR_DICT   = COLORS[LANG]
COLOR_NAMES  = list(COLOR_DICT.keys())
CORNERS      = ["top_left", "top_right", "bottom_left", "bottom_right"]
MAX_LEVELS   = 5

UI = {
    "es": {
        "title":        "LA BÚSQUEDA DEL VAQUERO",
        "subtitle":     "Evaluación Neuropsicológica Asistida",
        "patient_id":   "ID Paciente",
        "patient_age":  "Edad",
        "age_group":    "Grupo de edad",
        "start_level":  "Nivel de inicio",
        "btn_start":    "INICIAR MISIÓN",
        "btn_cal":      "CALIBRAR CÁMARA",
        "cal_title":    "CALIBRACIÓN DE CÁMARA",
        "cal_inst":     "Mueve tu mano por toda la pantalla durante 5 segundos",
        "cal_counting": "Capturando movimiento…",
        "cal_done":     "¡Calibración completa!",
        "cal_fail":     "Calibración insuficiente — intenta de nuevo",
        "instructions": "Señala el COLOR de la tinta, no lo que dice la palabra",
        "dwell_hint":   "Mantén el dedo 0.4s sobre la respuesta",
        "level_lbl":    "NIVEL",
        "timeout":      "⏱ TIEMPO AGOTADO",
        "next_level":   "ENTER para continuar al siguiente nivel",
        "finished":     "Misión completada — generando reporte clínico…",
        "score":        "Precisión",
        "patient":      "Paciente",
        "press_q":      "Q = Salir   ESC = Menú",
        "no_hand":      "✋ Muestra tu mano a la cámara",
        "congr_badge":  "CONGRUENTE",
        "incongr_badge":"INCONGRUENTE",
    }
}
T = UI.get(LANG, UI["es"])

# ── Helpers de render ─────────────────────────────────────────

def draw_rrect(surf, rect, color, radius=14, alpha=255):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]),
                     border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))

def lerp_col(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def text_centered(surf, font, text, color, cx, cy, shadow=False):
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        surf.blit(s, s.get_rect(center=(cx+2, cy+2)))
    lbl = font.render(text, True, color)
    surf.blit(lbl, lbl.get_rect(center=(cx, cy)))
    return lbl.get_rect(center=(cx, cy))


# ══════════════════════════════════════════════════════════════
class StroopGame:

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        if FULLSCREEN:
            info = pygame.display.Info()
            self.W, self.H = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((self.W, self.H), pygame.FULLSCREEN)
        else:
            self.W, self.H = 1280, 720
            self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("La Búsqueda del Vaquero (Stroop v2.2)")

        fw = max(30, int(self.H * FONT_WORD_SIZE_FRAC))
        fl = max(16, int(self.H * FONT_LABEL_SIZE_FRAC))
        self.f_word  = pygame.font.SysFont("Arial", fw, bold=True)
        self.f_label = pygame.font.SysFont("Arial", fl, bold=True)
        self.f_small = pygame.font.SysFont("Arial", fl - 2)
        self.f_tiny  = pygame.font.SysFont("Arial", max(13, fl - 6))
        self.f_big   = pygame.font.SysFont("Arial", fw + 10, bold=True)

        # ── Directorio Base Dinámico ──────────────────────────────────
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # ── Cargar Música ─────────────────────────────────────────────
        try:
            music_path = os.path.join(BASE_DIR, "quiet.mp3")
            pygame.mixer.music.load(music_path) 
            pygame.mixer.music.set_volume(0.3)     
            pygame.mixer.music.play(-1)            
        except Exception as e:
            print(f"Aviso: No se pudo cargar quiet.mp3: {e}")

        # ── Cargar Fondo del Menú ──────────────────────────────────────
        try:
            bg_path = os.path.join(BASE_DIR, "fondo_menu.jpg")
            raw_bg = pygame.image.load(bg_path).convert()
            self.menu_bg = pygame.transform.scale(raw_bg, (self.W, self.H))
        except Exception as e:
            print(f"Aviso: No se pudo cargar fondo_menu.jpg: {e}")
            self.menu_bg = None

        # ── Cargar Sprite del Vaquero ──────────────────────────────────
        try:
            img_path = os.path.join(BASE_DIR, "vaquero.png")
            raw_img = pygame.image.load(img_path).convert_alpha()
            w, h = raw_img.get_size()
            
            target_h = int(self.H * 0.40)
            target_w = int(w * (target_h / h)) 
            self.atenea_sprite = pygame.transform.scale(raw_img, (target_w, target_h))
        except Exception as e:
            print(f"Aviso: No se pudo cargar el sprite: {e}")
            self.atenea_sprite = pygame.Surface((200, 300))
            self.atenea_sprite.fill((100, 200, 200))
            text_centered(self.atenea_sprite, self.f_small, "Vaquero IMG", (0,0,0), 100, 150)
        
        self.intro_dialogue_step = 0 
        self._next_phase_after_intro = "trial"

        self.tracker = HandTracker()
        self.clock   = pygame.time.Clock()

        self.patient_id  = "PAC001"
        self.patient_age = 5
        self.age_group   = "toddler_assisted"
        self.start_level = 1
        self.recorder    = None  

        self.phase          = "intake"
        self.current_level  = 1
        self.trial_index    = 0
        self.level_stats    = {}

        self.word           = ""
        self.word_color     = ""
        self.word_color_rgb = (255,255,255)
        self.correct_answer = ""
        self.corner_map     = {}
        self.zone_rects     = {}

        self.feedback_text  = ""
        self.feedback_color = (255,255,255)
        self.feedback_until = 0
        self.last_rt_ms     = 0

        self.trial_start    = 0.0
        self.stimulus_shown = False
        self.decision_onset = None
        self._pause_start   = None

        self.finger_px   = None
        self.finger_py   = None
        self.cam_surface = None  
        self.particles = []

        self.cam_w = int(self.W * CAM_FEED_W_FRAC)
        self.cam_h = int(self.H * CAM_FEED_H_FRAC)
        self.cam_x = (self.W - self.cam_w) // 2
        self.cam_y = (self.H - self.cam_h) // 2 + 10

        self._intake_fields = {
            "id":    {"value": "PAC001",  "active": False, "label": T["patient_id"]},
            "age":   {"value": "5",       "active": False, "label": T["patient_age"]},
        }
        self._intake_level  = 1  
        self._click_zones   = {} # Almacenará coordenadas de la UI dinámicamente

        self._cal_phase    = "waiting"  
        self._cal_start    = 0.0
        self._cal_duration = 5.0        

    # ══════════════════════════════════════════════════════════
    #  UTILIDADES DE DIBUJO
    # ══════════════════════════════════════════════════════════
    def _draw_background(self):
        """Dibuja el fondo y el filtro oscuro en todas las pantallas"""
        if self.menu_bg:
            self.screen.blit(self.menu_bg, (0, 0))
            overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140)) 
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(BG_COLOR)

    def _update_camera(self):
        frame, fx, fy = self.tracker.get_frame_and_finger()
        if frame is None:
            self.finger_px = self.finger_py = None
            self.cam_surface = None
            return
        try:
            cam_small = cv2.resize(frame, (self.cam_w, self.cam_h))
            cam_rgb   = cv2.cvtColor(cam_small, cv2.COLOR_BGR2RGB)
            self.cam_surface = pygame.surfarray.make_surface(np.transpose(cam_rgb, (1, 0, 2)))
        except Exception:
            self.cam_surface = None

        if fx is not None and fy is not None:
            self.finger_px = int(fx * self.W)
            self.finger_py = int(fy * self.H)
        else:
            self.finger_px = self.finger_py = None

    # ══════════════════════════════════════════════════════════
    #  INTAKE (Menú Principal)
    # ══════════════════════════════════════════════════════════
    def _phase_intake(self):
        self._draw_background()
        self._click_zones.clear() # Limpiamos colisiones del frame anterior

        W, H = self.W, self.H

        text_centered(self.screen, self.f_big, T["title"], (255, 200, 80), W//2, H//8, shadow=True)
        text_centered(self.screen, self.f_small, T["subtitle"], (200, 200, 200), W//2, H//8+50, shadow=True)

        pw, ph = 600, 520  
        px, py = W//2 - pw//2, H//2 - ph//2 + 20
        draw_rrect(self.screen, (px, py, pw, ph), (20,20,30), radius=20, alpha=230)
        pygame.draw.rect(self.screen, (200, 150, 50), (px,py,pw,ph), 2, border_radius=20) 

        field_y = py + 40
        field_w = 400 
        field_x = W//2 - field_w//2

        # ID
        f_id  = self._intake_fields["id"]
        lbl   = self.f_small.render(f_id["label"], True, (160,160,200))
        self.screen.blit(lbl, (field_x, field_y))
        field_y += 35
        box_col = (80,130,200) if f_id["active"] else (50,50,80)
        draw_rrect(self.screen, (field_x, field_y, field_w, 45), box_col, alpha=200)
        pygame.draw.rect(self.screen, box_col, (field_x, field_y, field_w, 45), 2, border_radius=8)
        val = self.f_label.render(f_id["value"] + ("|" if f_id["active"] else ""), True, (255,255,255))
        self.screen.blit(val, (field_x+10, field_y+10))
        self._click_zones["id"] = pygame.Rect(field_x, field_y, field_w, 45)
        field_y += 70 

        # Edad
        f_age = self._intake_fields["age"]
        lbl   = self.f_small.render(f_age["label"], True, (160,160,200))
        self.screen.blit(lbl, (field_x, field_y))
        field_y += 35 
        box_col = (80,130,200) if f_age["active"] else (50,50,80)
        draw_rrect(self.screen, (field_x, field_y, field_w, 45), box_col, alpha=200)
        pygame.draw.rect(self.screen, box_col, (field_x, field_y, field_w, 45), 2, border_radius=8)
        val = self.f_label.render(f_age["value"] + ("|" if f_age["active"] else ""), True, (255,255,255))
        self.screen.blit(val, (field_x+10, field_y+10))
        self._click_zones["age"] = pygame.Rect(field_x, field_y, field_w, 45)
        field_y += 70 

        # Nivel
        lbl = self.f_small.render(T["start_level"], True, (160,160,200))
        self.screen.blit(lbl, (field_x, field_y))
        field_y += 35 
        btn_w = 65 
        for lvl in range(1, MAX_LEVELS+1):
            bx = field_x + (lvl-1)*(btn_w+18) 
            selected = (lvl == self._intake_level)
            bcol = (80,140,220) if selected else (35,35,60)
            draw_rrect(self.screen, (bx, field_y, btn_w, 45), bcol, radius=10, alpha=230)
            pygame.draw.rect(self.screen, (80,80,140) if not selected else (120,180,255), (bx, field_y, btn_w, 45), 1, border_radius=10)
            text_centered(self.screen, self.f_small, str(lvl), (255,255,255), bx+btn_w//2, field_y+22)
            self._click_zones[f"lvl_{lvl}"] = pygame.Rect(bx, field_y, btn_w, 45)
        field_y += 100 

        # Botones de Acción
        rect_cal = pygame.Rect(field_x, field_y, field_w//2-10, 50)
        rect_start = pygame.Rect(field_x+field_w//2+10, field_y, field_w//2-10, 50)
        
        self._click_zones["btn_cal"] = rect_cal
        self._click_zones["btn_start"] = rect_start

        draw_rrect(self.screen, rect_cal,   (40,80,120), radius=12,alpha=230)
        draw_rrect(self.screen, rect_start, (200,120,50), radius=12,alpha=230)
        pygame.draw.rect(self.screen,(80,140,200), rect_cal,  1,border_radius=12)
        pygame.draw.rect(self.screen,(255,200,100), rect_start,1,border_radius=12)

        text_centered(self.screen, self.f_small, T["btn_cal"], (200,230,255), rect_cal.centerx, rect_cal.centery)
        text_centered(self.screen, self.f_small, T["btn_start"], (255,255,255), rect_start.centerx, rect_start.centery)

        # Lógica de clicks garantizada por _click_zones
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: self._quit()
                if event.key == pygame.K_TAB:
                    keys = ["id","age"]
                    active = next((k for k,v in self._intake_fields.items() if v["active"]), None)
                    for f in self._intake_fields.values(): f["active"] = False
                    if active:
                        nxt = keys[(keys.index(active)+1) % len(keys)]
                        self._intake_fields[nxt]["active"] = True
                    else:
                        self._intake_fields["id"]["active"] = True

                active_f = next((v for v in self._intake_fields.values() if v["active"]), None)
                if active_f:
                    if event.key == pygame.K_BACKSPACE:
                        active_f["value"] = active_f["value"][:-1]
                    elif event.key == pygame.K_RETURN:
                        active_f["active"] = False
                    elif event.unicode.isprintable() and len(active_f["value"]) < 20:
                        active_f["value"] += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # Desactivar campos por defecto
                for k in self._intake_fields: self._intake_fields[k]["active"] = False
                
                if self._click_zones.get("id") and self._click_zones["id"].collidepoint(mx,my):
                    self._intake_fields["id"]["active"] = True
                elif self._click_zones.get("age") and self._click_zones["age"].collidepoint(mx,my):
                    self._intake_fields["age"]["active"] = True

                for lvl in range(1, MAX_LEVELS+1):
                    if self._click_zones.get(f"lvl_{lvl}") and self._click_zones[f"lvl_{lvl}"].collidepoint(mx,my):
                        self._intake_level = lvl

                if self._click_zones.get("btn_cal") and self._click_zones["btn_cal"].collidepoint(mx,my):
                    self.intro_dialogue_step = 0
                    self._next_phase_after_intro = "calibration"
                    self.phase = "intro"
                if self._click_zones.get("btn_start") and self._click_zones["btn_start"].collidepoint(mx,my):
                    self._launch_session() 
                    self.intro_dialogue_step = 0
                    self._next_phase_after_intro = "trial"
                    self.phase = "intro"

    # ══════════════════════════════════════════════════════════
    #  FASE: INTRODUCCIÓN NARRATIVA
    # ══════════════════════════════════════════════════════════
    def _phase_intro(self):
        self._draw_background()
        
        sprite_x = 40
        sprite_y = self.H - self.atenea_sprite.get_height() - 20
        self.screen.blit(self.atenea_sprite, (sprite_x, sprite_y))

        box_x = sprite_x + self.atenea_sprite.get_width() + 30
        box_w = self.W - box_x - 40  
        box_h = 180
        box_y = self.H - box_h - 40

        draw_rrect(self.screen, (box_x, box_y, box_w, box_h), (20, 20, 40), radius=15, alpha=230)
        pygame.draw.rect(self.screen, (200, 150, 50), (box_x, box_y, box_w, box_h), 3, border_radius=15)

        name_lbl = self.f_label.render("VAQUERO", True, (255, 200, 80))
        self.screen.blit(name_lbl, (box_x + 20, box_y + 15))

        dialogues = [
            ["¡Hola vaquerito! Qué bueno verte por aquí.", "Necesito tu ayuda para una misión muy importante."],
            ["Van a aparecer unos animales y colores mágicos.", "Solo tienes que tocar el correcto lo más rápido posible."],
            ["¡Demuéstrame esos reflejos de forajido!", "¿Estás listo?"]
        ]

        if self.intro_dialogue_step < len(dialogues):
            current_lines = dialogues[self.intro_dialogue_step]
            line_y = box_y + 60
            for line in current_lines:
                txt_surf = self.f_small.render(line, True, (255, 255, 255))
                self.screen.blit(txt_surf, (box_x + 20, line_y))
                line_y += 40
            
            hint = self.f_tiny.render("ENTER o Clic para continuar >", True, (150, 150, 150))
            self.screen.blit(hint, (box_x + box_w - hint.get_width() - 20, box_y + box_h - 30))
        else:
            self.phase = self._next_phase_after_intro
            if self.phase == "calibration":
                self._cal_phase = "waiting"

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: self._quit()
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.intro_dialogue_step += 1
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.intro_dialogue_step += 1

    # ══════════════════════════════════════════════════════════
    #  CALIBRACIÓN Y SESIÓN (Recortado visualmente igual, lógica intacta)
    # ══════════════════════════════════════════════════════════
    def _phase_calibration(self):
        self._update_camera()
        self._draw_background()

        if self.cam_surface:
            self.screen.blit(self.cam_surface, (self.cam_x, self.cam_y))

        text_centered(self.screen, self.f_label, T["cal_title"], (180,180,255), self.W//2, 40)

        if self._cal_phase == "waiting":
            text_centered(self.screen, self.f_small, T["cal_inst"], (200,200,200), self.W//2, self.H-80)
            hint = self.f_tiny.render("Clic / ENTER para comenzar", True, (120,200,120))
            self.screen.blit(hint, hint.get_rect(center=(self.W//2, self.H-50)))

        elif self._cal_phase == "recording":
            elapsed = time.perf_counter() - self._cal_start
            remain  = max(0, self._cal_duration - elapsed)
            prog = min(elapsed / self._cal_duration, 1.0)
            bar_w = int(self.W * 0.6 * prog)
            pygame.draw.rect(self.screen, (40,40,70), (self.W//2-self.W//5*3//2, self.H-55, int(self.W*0.6), 20), border_radius=10)
            pygame.draw.rect(self.screen, (80,200,120), (self.W//2-self.W//5*3//2, self.H-55, bar_w, 20), border_radius=10)
            text_centered(self.screen, self.f_small, f"{T['cal_counting']}  {remain:.1f}s", (200,240,200), self.W//2, self.H-25)

            ret, raw = self.tracker._cap.read()
            if ret:
                frame_out, fx, fy = self.tracker.update_calibration(raw)

            if elapsed >= self._cal_duration:
                ok = self.tracker.finalize_calibration()
                self._cal_phase = "done" if ok else "fail"

        elif self._cal_phase == "done":
            text_centered(self.screen, self.f_label, T["cal_done"], (80,220,100), self.W//2, self.H-60)
            hint = self.f_tiny.render("ENTER o clic para volver", True,(160,200,160))
            self.screen.blit(hint, hint.get_rect(center=(self.W//2, self.H-30)))

        elif self._cal_phase == "fail":
            text_centered(self.screen, self.f_label, T["cal_fail"], (220,100,80), self.W//2, self.H-60)
            hint = self.f_tiny.render("ENTER o clic para reintentar",True,(200,160,160))
            self.screen.blit(hint, hint.get_rect(center=(self.W//2, self.H-30)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                key = getattr(event, "key", None)
                if key == pygame.K_q: self._quit()
                if self._cal_phase == "waiting":
                    self.tracker.start_calibration()
                    self._cal_start = time.perf_counter()
                    self._cal_phase = "recording"
                elif self._cal_phase in ("done","fail"):
                    if self._cal_phase == "fail":
                        self._cal_phase = "waiting"
                    else:
                        self.phase = "intake"

    def _launch_session(self):
        self.patient_id  = self._intake_fields["id"]["value"].strip() or "PAC001"
        try:
            self.patient_age = int(self._intake_fields["age"]["value"])
        except Exception:
            self.patient_age = 25
        self.age_group   = get_age_group(self.patient_age)
        self.start_level = self._intake_level
        self.recorder    = DataRecorder(patient_id=self.patient_id, age_group=self.age_group)
        self.level_stats = {}
        self.current_level = self.start_level
        self.trial_index   = 0
        self.level_stats[self.current_level] = {"correct":0,"total":0}
        self._new_trial()

    # ══════════════════════════════════════════════════════════
    #  NÚCLEO DEL JUEGO Y RENDER
    # ══════════════════════════════════════════════════════════
    def _compute_corner_rects(self, size_frac):
        sz  = int(self.H * size_frac)
        pad = int(self.H * 0.08)
        return {
            "top_left":     pygame.Rect(pad,           pad,           sz, sz),
            "top_right":    pygame.Rect(self.W-pad-sz, pad,           sz, sz),
            "bottom_left":  pygame.Rect(pad,           self.H-pad-sz, sz, sz),
            "bottom_right": pygame.Rect(self.W-pad-sz, self.H-pad-sz, sz, sz),
        }

    def _new_trial(self):
        lvl_cfg = get_level_config(self.age_group, self.current_level)
        names   = COLOR_NAMES.copy()

        if lvl_cfg["incongruent"]:
            self.word       = random.choice(names)
            rest            = [n for n in names if n != self.word]
            self.word_color = random.choice(rest)
        else:
            self.word       = random.choice(names)
            self.word_color = self.word

        self.word_color_rgb = COLOR_DICT[self.word_color]
        self.correct_answer = self.word_color

        shuffled = names.copy()
        random.shuffle(shuffled)
        self.corner_map = {pos: col for pos, col in zip(CORNERS, shuffled)}

        corner_rects  = self._compute_corner_rects(lvl_cfg["target_size"])
        self.zone_rects = {self.corner_map[pos]: corner_rects[pos] for pos in CORNERS}

        self.stimulus_shown = False
        self.trial_start    = 0.0
        self.decision_onset = None
        self._pause_start   = None
        self.tracker.start_trial()

    def _draw_zones(self, dwell_zone, dwell_progress):
        lvl_cfg      = get_level_config(self.age_group, self.current_level)
        corner_rects = self._compute_corner_rects(lvl_cfg["target_size"])

        for pos, color_name in self.corner_map.items():
            rect      = corner_rects[pos]
            color_rgb = COLOR_DICT[color_name]
            is_hover  = (self.finger_px is not None and rect.collidepoint(self.finger_px, self.finger_py))

            draw_rrect(self.screen, rect, color_rgb, radius=22, alpha=185 if is_hover else 130)
            pygame.draw.rect(self.screen, (255,255,255) if is_hover else (80,80,110), rect, 3 if is_hover else 1, border_radius=22)

            if is_hover and dwell_progress > 0:
                cx, cy = rect.centerx, rect.centery
                r      = rect.width // 2 + 10
                arc_r  = pygame.Rect(cx-r, cy-r, r*2, r*2)
                pygame.draw.arc(self.screen, (255,255,255), arc_r, math.radians(-90), math.radians(-90 + 360*dwell_progress), 4)

            lbl = self.f_label.render(color_name, True, (255,255,255))
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_cam_feed(self):
        frame_rect = pygame.Rect(self.cam_x-3, self.cam_y-3, self.cam_w+6, self.cam_h+6)
        pygame.draw.rect(self.screen, (200, 150, 50), frame_rect, 3, border_radius=6)

        if self.cam_surface:
            self.screen.blit(self.cam_surface, (self.cam_x, self.cam_y))
        else:
            draw_rrect(self.screen, (self.cam_x, self.cam_y, self.cam_w, self.cam_h), (20,20,35), radius=4, alpha=200)
            msg = self.f_small.render("Sin señal de cámara", True, (120,80,80))
            self.screen.blit(msg, msg.get_rect(center=(self.cam_x+self.cam_w//2, self.cam_y+self.cam_h//2)))

    def _draw_stimulus(self):
        cx = self.W // 2
        cy = self.cam_y + self.cam_h // 2
        txt_surf = self.f_word.render(self.word, True, self.word_color_rgb)
        tw, th   = txt_surf.get_size()
        halo     = pygame.Surface((tw+50, th+26), pygame.SRCALPHA)
        halo.fill((0, 0, 0, 150))
        self.screen.blit(halo, (cx - tw//2 - 25, cy - th//2 - 13))
        self.screen.blit(txt_surf, txt_surf.get_rect(center=(cx, cy)))

    def _draw_finger_cursor(self):
        if self.finger_px is None: return
        pygame.draw.circle(self.screen, (255,255,255), (self.finger_px, self.finger_py), 9)
        pygame.draw.circle(self.screen, (255,220,60), (self.finger_px, self.finger_py), 15, 2)

    def _draw_hud(self):
        lvl_cfg  = get_level_config(self.age_group, self.current_level)
        lvl_name = LEVEL_NAMES[LANG][self.current_level]
        ag_lbl   = AGE_GROUPS[self.age_group]["label"][LANG]

        top = self.f_small.render(f"{T['level_lbl']} {self.current_level} — {lvl_name}  |  {ag_lbl}", True, (160,160,210))
        self.screen.blit(top, (10, 8))

        total = lvl_cfg["trials"]
        tr_t  = self.f_tiny.render(f"{self.trial_index}/{total}", True, (120,120,160))
        self.screen.blit(tr_t, (10, 8+top.get_height()+2))

        pat = self.f_tiny.render(f"{T['patient']}: {self.patient_id}", True, (100,100,140))
        self.screen.blit(pat, (self.W - pat.get_width() - 10, 8))

        inst = self.f_tiny.render(T["instructions"], True, (200,200,200))
        self.screen.blit(inst, inst.get_rect(centerx=self.W//2, top=8))

        if self.finger_px is None and self.stimulus_shown:
            warn = self.f_small.render(T["no_hand"], True, (220,160,50))
            self.screen.blit(warn, warn.get_rect(center=(self.W//2, self.cam_y + self.cam_h + 18)))

        stats = self.level_stats.get(self.current_level,{"correct":0,"total":0})
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
            sc  = self.f_tiny.render(f"{T['score']}: {acc:.0f}%", True, (80,220,100) if acc >= 80 else (220,140,60))
            self.screen.blit(sc, sc.get_rect(centerx=self.W//2, bottom=self.H - TIMER_BAR_HEIGHT - 6))

    def _draw_timer_bar(self, elapsed, time_limit):
        ratio = max(0, 1 - elapsed / time_limit)
        bw    = int(self.W * ratio)
        col   = lerp_col((220,50,50), (50,200,100), ratio)
        pygame.draw.rect(self.screen, (30,30,50), (0, self.H-TIMER_BAR_HEIGHT, self.W, TIMER_BAR_HEIGHT))
        if bw > 0:
            pygame.draw.rect(self.screen, col, (0, self.H-TIMER_BAR_HEIGHT, bw, TIMER_BAR_HEIGHT))

    def _spawn_particles(self, x, y, color):
        for _ in range(20):
            a = random.uniform(0, 2*math.pi)
            s = random.uniform(2, 9)
            self.particles.append({"x":x,"y":y,"vx":math.cos(a)*s,"vy":math.sin(a)*s, "life":1.0,"color":color,"r":random.randint(3,7)})

    def _update_draw_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            p["vy"] += 0.2; p["life"] -= 0.04
        self.particles = [p for p in self.particles if p["life"] > 0]
        for p in self.particles:
            s = pygame.Surface((p["r"]*2,p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s,(*p["color"],int(p["life"]*255)), (p["r"],p["r"]),p["r"])
            self.screen.blit(s,(int(p["x"])-p["r"],int(p["y"])-p["r"]))

    def _phase_trial(self):
        lvl_cfg = get_level_config(self.age_group, self.current_level)
        elapsed = (time.perf_counter() - self.trial_start if self.stimulus_shown else 0)

        self._draw_background()
        self._update_draw_particles()
        self._draw_cam_feed()

        if self.stimulus_shown:
            dwell_name, dwell_prog = self.tracker.check_dwell_px(self.finger_px, self.finger_py, self.zone_rects)
            self._draw_zones(dwell_name, dwell_prog)
            self._draw_stimulus()
            self._draw_timer_bar(elapsed, lvl_cfg["time_limit"])
            self._draw_hud()
            self._draw_finger_cursor()

            if self.decision_onset is None and self.finger_px is not None:
                self.decision_onset = (time.perf_counter()-self.trial_start)*1000

            if elapsed >= lvl_cfg["time_limit"]:
                self._end_trial(None, timed_out=True)
                return
            if dwell_name:
                self._end_trial(dwell_name, timed_out=False)
                return
        else:
            cross = self.f_word.render("+", True, (255,255,255))
            self.screen.blit(cross, cross.get_rect(center=(self.W//2, self.cam_y+self.cam_h//2)))
            self._draw_hud()
            if self._pause_start is None:
                self._pause_start = time.perf_counter()
            if time.perf_counter() - self._pause_start > 0.5:
                self.stimulus_shown = True
                self.trial_start    = time.perf_counter()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:    self._quit()
                if event.key == pygame.K_ESCAPE: self.phase = "intake"

    def _end_trial(self, response, timed_out):
        lvl_cfg = get_level_config(self.age_group, self.current_level)
        rt_ms   = (time.perf_counter() - self.trial_start) * 1000

        motor = self.tracker.end_trial()
        correct = self.recorder.record_trial(
            level=self.current_level, word=self.word,
            word_color=self.word_color, word_color_rgb=self.word_color_rgb,
            correct_answer=self.correct_answer,
            congruent=not lvl_cfg["incongruent"],
            response=response, rt_ms=rt_ms,
            decision_onset_ms=self.decision_onset or 0,
            timed_out=timed_out, motor_metrics=motor,
            time_limit_s=lvl_cfg["time_limit"])

        if self.current_level not in self.level_stats:
            self.level_stats[self.current_level] = {"correct":0,"total":0}
        self.level_stats[self.current_level]["total"]  += 1
        
        # SISTEMA DE ALIENTO DEL VAQUERO
        if timed_out:
            self.feedback_text  = random.choice(["¡El tiempo vuela!", "¡Más rápido la próxima!"])
            self.feedback_color = (255,200,50)
        elif correct:
            self.level_stats[self.current_level]["correct"] += 1
            self.feedback_text  = random.choice(["¡Qué puntería, vaquerito!", "¡Ese es mi muchacho!", "¡Más rápido que mi sombra!"])
            self.feedback_color = (80,220,100)
            if self.finger_px:
                self._spawn_particles(self.finger_px,self.finger_py,(80,220,100))
        else:
            self.feedback_text  = random.choice(["¡Casi, inténtalo de nuevo!", "¡No te rindas, vaquerito!", "¡Concéntrate en el color!"])
            self.feedback_color = (220,80,80)

        self.last_rt_ms     = rt_ms
        self.feedback_until = time.perf_counter() + 1.8 # Aumentado a 1.8s para que lean el diálogo
        self.phase          = "feedback"

    # ══════════════════════════════════════════════════════════
    #  FASE: FEEDBACK (Ahora interactiva con el Vaquero)
    # ══════════════════════════════════════════════════════════
    def _phase_feedback(self):
        self._draw_background()
        self._update_draw_particles()
        self._draw_cam_feed()

        # Dibujar al Vaquero
        sprite_x = 40
        sprite_y = self.H - self.atenea_sprite.get_height() - 20
        self.screen.blit(self.atenea_sprite, (sprite_x, sprite_y))

        # Globo de texto de Feedback
        box_x = sprite_x + self.atenea_sprite.get_width() + 20
        box_w = self.f_word.size(self.feedback_text)[0] + 60
        box_h = 100
        box_y = self.H - box_h - 40

        draw_rrect(self.screen, (box_x, box_y, box_w, box_h), (20, 20, 40), radius=15, alpha=230)
        pygame.draw.rect(self.screen, self.feedback_color, (box_x, box_y, box_w, box_h), 3, border_radius=15)

        fb = self.f_word.render(self.feedback_text, True, self.feedback_color)
        self.screen.blit(fb, fb.get_rect(center=(box_x + box_w//2, box_y + box_h//2)))

        rt  = self.f_small.render(f"RT: {self.last_rt_ms:.0f} ms", True,(200,200,200))
        self.screen.blit(rt, rt.get_rect(center=(self.cam_x + self.cam_w//2, self.cam_y + self.cam_h + 30)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()

        if time.perf_counter() >= self.feedback_until:
            self.trial_index += 1
            lvl_cfg = get_level_config(self.age_group, self.current_level)
            if self.trial_index >= lvl_cfg["trials"]:
                if self.current_level < MAX_LEVELS:
                    self.phase = "level_results"
                else:
                    self.phase = "end"
            else:
                self._new_trial()
                self.phase = "trial"

    def _phase_level_results(self):
        self._draw_background()
        stats = self.level_stats.get(self.current_level,{"correct":0,"total":1})
        acc   = stats["correct"] / max(stats["total"],1) * 100

        text_centered(self.screen, self.f_word, f"{T['level_lbl']} {self.current_level} — {LEVEL_NAMES[LANG][self.current_level]}", (255,200,80), self.W//2, self.H//2-90, shadow=True)
        text_centered(self.screen, self.f_label, f"{T['score']}: {acc:.1f}%", (80,220,100) if acc>=80 else (220,120,80), self.W//2, self.H//2)

        grp     = AGE_GROUPS[self.age_group]
        norm_acc= grp.get("norm_accuracy", 0)
        diff    = acc - norm_acc
        norm_t  = self.f_small.render(f"Norma grupo edad: {norm_acc}%   Diferencia: {diff:+.1f}%", True, (160,200,160))
        self.screen.blit(norm_t, norm_t.get_rect(center=(self.W//2, self.H//2+50)))

        cont = self.f_small.render(T["next_level"], True, (255,255,255))
        self.screen.blit(cont, cont.get_rect(center=(self.W//2, self.H//2+100)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self._quit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.current_level += 1
                    self.trial_index   = 0
                    if self.current_level not in self.level_stats:
                        self.level_stats[self.current_level] = {"correct":0,"total":0}
                    self._new_trial()
                    self.phase = "trial"

    def _phase_end(self):
        self._draw_background()
        msg = self.f_label.render(T["finished"], True, (255,200,80))
        self.screen.blit(msg, msg.get_rect(center=(self.W//2,self.H//2)))
        pygame.display.flip()

        summary = self.recorder.get_summary()
        trials  = self.recorder.get_all_trials()
        pdf     = generate_full_report(summary, trials, patient_id=self.patient_id, age_group=self.age_group)
        self._draw_background()
        text_centered(self.screen, self.f_label, "✓ Reporte generado", (80,220,100), self.W//2, self.H//2-20)
        p_lbl = self.f_tiny.render(pdf, True, (200,200,200))
        self.screen.blit(p_lbl, p_lbl.get_rect(center=(self.W//2, self.H//2+30)))
        q_lbl = self.f_small.render("Q para salir", True, (255,255,255))
        self.screen.blit(q_lbl, q_lbl.get_rect(center=(self.W//2, self.H//2+80)))
        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self._quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    self._quit()
            self.clock.tick(30)

    # ══════════════════════════════════════════════════════════
    #  LOOP PRINCIPAL
    # ══════════════════════════════════════════════════════════
    def run(self):
        while True:
            if self.phase not in ("intake", "intro", "calibration"):
                self._update_camera()

            if   self.phase == "intake":        self._phase_intake()
            elif self.phase == "intro":         self._phase_intro()
            elif self.phase == "calibration":   self._phase_calibration()
            elif self.phase == "trial":         self._phase_trial()
            elif self.phase == "feedback":      self._phase_feedback()
            elif self.phase == "level_results": self._phase_level_results()
            elif self.phase == "end":           self._phase_end()

            pygame.display.flip()
            self.clock.tick(60)

    def _quit(self):
        try: self.tracker.release()
        except Exception: pass
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    StroopGame().run()
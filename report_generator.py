"""
report_generator.py  v2.4 — Edición Mission Brain (Bilingüe)
────────────────────────
Igual que v2.3 + Soporte dinámico para reportes en Inglés/Español 
(títulos, tablas, gráficos y observaciones automáticas) según config.py.
"""

import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage,
                                 HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from config import REPORTS_DIR, PATIENT_ID, LANGUAGE, AGE_GROUPS, LEVEL_NAMES

PALETTE = {1:"#4CAF50",2:"#2196F3",3:"#FF9800",4:"#E91E63",5:"#9C27B0"}
DARK_BG  = "#0d0d1a"
DARK_AX  = "#1a1a2e"

# ── DICCIONARIO DE TRADUCCIÓN ──────────────────────────────────────────────
REPORT_TXT = {
    "es": {
        "title": "La Búsqueda del Vaquero - Stroop v2.4",
        "subtitle": "Reporte Clínico de Evaluación Neuropsicológica Asistida",
        "patient": "Paciente",
        "date": "Fecha",
        "age_group": "Grupo edad",
        "trials": "Ensayos",
        "corrects": "Correctos",
        "timeouts": "Timeouts",
        "rt_global": "RT global",
        "norm_rt_inc": "Norma RT inc",
        "lat_title": "Evaluación de Lateralidad y Asimetría",
        "hand_used": "Mano Utilizada",
        "accuracy": "Precisión",
        "rt_avg": "RT Promedio",
        "right": "Derecha",
        "left": "Izquierda",
        "not_detected": "No detectada",
        "stroop_title": "Métricas Neuropsicológicas Stroop",
        "level": "Nivel",
        "std_rt": "σ RT",
        "interference": "Interferencia",
        "tremor": "Temblor",
        "corrections": "Correcciones",
        "visual_analysis": "Análisis Visual",
        "chart_norm": "Comparación con Norma del Grupo de Edad",
        "chart_rt": "Tiempo de Reacción por Nivel",
        "chart_acc": "Precisión por Nivel",
        "chart_learn": "Evolución del RT",
        "chart_motor": "Métricas Motoras",
        "obs_title": "Observaciones Automáticas",
        "obs_asymmetry": "• ASIMETRÍA MOTORA DETECTADA: La mano {lenta} presenta una lentitud relativa de {rt_diff:.0f} ms frente a la contralateral. Evaluar posible hemiparesia o dominancia forzada.",
        "obs_rt_inc": "• RT aumentó {diff:.0f} ms del nivel 1 al nivel {lvl} ({rt1:.0f} → {rtL:.0f} ms).",
        "obs_interf": "• Nivel {lvl} — Índice de interferencia: {interf:+.0f} ms (norma: {norm:+.0f} ms) → {flag}.",
        "obs_acc_low": "• Nivel {lvl}: precisión baja ({acc}%). Posible dificultad de control inhibitorio.",
        "obs_tremor": "• Nivel {lvl}: temblor elevado ({tremor:.4f}). Revisar función motora fina.",
        "obs_timeout": "• Nivel {lvl}: {timeouts} timeouts. Tiempo límite podría requerir ajuste para este paciente.",
        "obs_none": "• Sin observaciones destacadas.",
        "obs_disclaimer": "\n⚠️ Herramienta de apoyo diagnóstico para cribado de TBI. Interpretación clínica a cargo de profesional certificado.",
        "high": "elevado",
        "normal": "normal",
        "threshold": "Umbral 80%",
        "patient_legend": "Paciente",
        "norm_legend": "Norma",
        "chart_rt_y": "RT promedio (ms)",
        "chart_acc_y": "Precisión (%)",
        "chart_learn_x": "Ensayo",
        "chart_learn_y": "RT (ms)",
        "tremor_idx": "Índice de Temblor",
        "motor_corr": "Correcciones Motoras",
        "rt_cong": "RT Congruente",
        "rt_incong": "RT Incongruente",
        "patient_vs_norm": "Paciente vs. Norma del Grupo de Edad",
        "na": "N/A"
    },
    "en": {
        "title": "The Cowboy's Quest - Stroop v2.4",
        "subtitle": "Assisted Neuropsychological Assessment Clinical Report",
        "patient": "Patient",
        "date": "Date",
        "age_group": "Age Group",
        "trials": "Trials",
        "corrects": "Correct",
        "timeouts": "Timeouts",
        "rt_global": "Overall RT",
        "norm_rt_inc": "Inc. RT Norm",
        "lat_title": "Lateralization and Asymmetry Assessment",
        "hand_used": "Hand Used",
        "accuracy": "Accuracy",
        "rt_avg": "Avg RT",
        "right": "Right",
        "left": "Left",
        "not_detected": "Not detected",
        "stroop_title": "Stroop Neuropsychological Metrics",
        "level": "Level",
        "std_rt": "RT σ",
        "interference": "Interference",
        "tremor": "Tremor",
        "corrections": "Corrections",
        "visual_analysis": "Visual Analysis",
        "chart_norm": "Age Group Norm Comparison",
        "chart_rt": "Reaction Time by Level",
        "chart_acc": "Accuracy by Level",
        "chart_learn": "RT Evolution",
        "chart_motor": "Motor Metrics",
        "obs_title": "Automated Observations",
        "obs_asymmetry": "• MOTOR ASYMMETRY DETECTED: The {lenta} hand shows a relative slowness of {rt_diff:.0f} ms compared to the contralateral hand. Evaluate possible hemiparesis or forced dominance.",
        "obs_rt_inc": "• RT increased by {diff:.0f} ms from level 1 to level {lvl} ({rt1:.0f} → {rtL:.0f} ms).",
        "obs_interf": "• Level {lvl} — Interference index: {interf:+.0f} ms (norm: {norm:+.0f} ms) → {flag}.",
        "obs_acc_low": "• Level {lvl}: low accuracy ({acc}%). Possible inhibitory control difficulty.",
        "obs_tremor": "• Level {lvl}: elevated tremor ({tremor:.4f}). Review fine motor function.",
        "obs_timeout": "• Level {lvl}: {timeouts} timeouts. Time limit may require adjustment for this patient.",
        "obs_none": "• No notable observations.",
        "obs_disclaimer": "\n⚠️ Diagnostic support tool for TBI screening. Clinical interpretation must be performed by a certified professional.",
        "high": "high",
        "normal": "normal",
        "threshold": "80% Threshold",
        "patient_legend": "Patient",
        "norm_legend": "Norm",
        "chart_rt_y": "Average RT (ms)",
        "chart_acc_y": "Accuracy (%)",
        "chart_learn_x": "Trial",
        "chart_learn_y": "RT (ms)",
        "tremor_idx": "Tremor Index",
        "motor_corr": "Motor Corrections",
        "rt_cong": "Congruent RT",
        "rt_incong": "Incongruent RT",
        "patient_vs_norm": "Patient vs. Age Group Norm",
        "na": "N/A"
    }
}

TXT = REPORT_TXT.get(LANGUAGE, REPORT_TXT["en"])

def _lname(lvl):
    return LEVEL_NAMES.get(LANGUAGE, LEVEL_NAMES["en"]).get(lvl, str(lvl))

def _dark_fig(figsize=(9, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_AX)
    ax.tick_params(colors="white")
    for sp in ax.spines.values():
        sp.set_edgecolor("#333")
    return fig, ax

def _dark_fig2(figsize=(12, 4)):
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    fig.patch.set_facecolor(DARK_BG)
    for ax in axes:
        ax.set_facecolor(DARK_AX)
        ax.tick_params(colors="white")
        for sp in ax.spines.values():
            sp.set_edgecolor("#333")
    return fig, axes


def generate_charts(summary, trials, age_group, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths  = {}
    levels = sorted(summary.keys())
    cols   = [PALETTE.get(l, "#888") for l in levels]
    names  = [f"Nv.{l}\n{_lname(l)}" for l in levels]

    # 1 ── RT por nivel
    fig, ax = _dark_fig()
    means = [summary[l]["mean_rt_ms"] for l in levels]
    bars  = ax.bar(names, means, color=cols, edgecolor="white", linewidth=0.8)
    ax.set_ylabel(TXT["chart_rt_y"], color="white")
    ax.set_title(TXT["chart_rt"], color="white", fontweight="bold")
    ax.yaxis.label.set_color("white")
    for bar, val in zip(bars, means):
        ax.text(bar.get_x()+bar.get_width()/2, val+12,
                f"{val:.0f}", ha="center", color="white", fontsize=8)
    p = os.path.join(out_dir, "chart_rt.png")
    fig.tight_layout(); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    paths["rt"] = p

    # 2 ── Precisión
    fig, ax = _dark_fig()
    accs = [summary[l]["accuracy_pct"] for l in levels]
    bars = ax.bar(names, accs, color=cols, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0, 115)
    ax.axhline(80, color="#FF5722", ls="--", alpha=0.7, label=TXT["threshold"])
    ax.legend(facecolor=DARK_AX, labelcolor="white")
    ax.set_ylabel(TXT["chart_acc_y"], color="white")
    ax.set_title(TXT["chart_acc"], color="white", fontweight="bold")
    ax.yaxis.label.set_color("white")
    for bar, val in zip(bars, accs):
        ax.text(bar.get_x()+bar.get_width()/2, val+1,
                f"{val:.1f}%", ha="center", color="white", fontsize=8)
    p = os.path.join(out_dir, "chart_accuracy.png")
    fig.tight_layout(); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    paths["accuracy"] = p

    # 3 ── Curva de aprendizaje
    fig, ax = _dark_fig((11, 4))
    for lvl in levels:
        pts = [(t["trial_number"], t["rt_ms"])
               for t in trials if t["level"] == lvl and not t["timed_out"]]
        if pts:
            ns, rs = zip(*pts)
            ax.scatter(ns, rs, color=PALETTE.get(lvl,"#888"), s=35, alpha=0.75,
                       label=f"Nv.{lvl}")
            wnd = 3
            if len(rs) >= wnd:
                ma = [sum(rs[max(0,i-wnd):i+1])/len(rs[max(0,i-wnd):i+1])
                      for i in range(len(rs))]
                ax.plot(ns, ma, color=PALETTE.get(lvl,"#888"), lw=1.5)
    ax.set_xlabel(TXT["chart_learn_x"], color="white")
    ax.set_ylabel(TXT["chart_learn_y"], color="white")
    ax.set_title(TXT["chart_learn"], color="white", fontweight="bold")
    ax.xaxis.label.set_color("white")
    ax.legend(facecolor=DARK_AX, labelcolor="white", fontsize=8)
    p = os.path.join(out_dir, "chart_learning.png")
    fig.tight_layout(); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    paths["learning"] = p

    # 4 ── Métricas motoras
    if len(levels) >= 2:
        fig, axes = _dark_fig2()
        for ax, key, lbl in zip(axes,
                                 ["mean_tremor","mean_corrections"],
                                 [TXT["tremor_idx"], TXT["motor_corr"]]):
            vals = [summary[l].get(key, 0) for l in levels]
            ax.bar(names, vals, color=cols, edgecolor="white", linewidth=0.8)
            ax.set_title(lbl, color="white", fontweight="bold")
            ax.yaxis.label.set_color("white")
        p = os.path.join(out_dir, "chart_motor.png")
        fig.tight_layout(); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
        paths["motor"] = p

    # 5 ── Comparación normativa
    grp = AGE_GROUPS.get(age_group, {})
    if grp and len(levels) >= 2:
        fig, ax = _dark_fig((9, 4.5))
        rt_cong   = summary.get(1, {}).get("mean_rt_ms", 0)
        rt_incong = max((summary.get(l, {}).get("mean_rt_ms", 0)
                         for l in levels if l > 1), default=0)
        norm_cong   = grp.get("norm_rt_congruent", 0)
        norm_incong = grp.get("norm_rt_incongruent", 0)

        categories = [TXT["rt_cong"], TXT["rt_incong"]]
        patient_v  = [rt_cong, rt_incong]
        norm_v     = [norm_cong, norm_incong]
        x          = range(len(categories))
        w          = 0.35

        ax.bar([i - w/2 for i in x], patient_v, w,
               color="#42A5F5", label=TXT["patient_legend"], edgecolor="white", linewidth=0.8)
        ax.bar([i + w/2 for i in x], norm_v, w,
               color="#78909C", label=f"{TXT['norm_legend']} ({grp['label'][LANGUAGE]})",
               edgecolor="white", linewidth=0.8)
        ax.set_xticks(list(x)); ax.set_xticklabels(categories, color="white")
        ax.set_ylabel("ms", color="white")
        ax.yaxis.label.set_color("white")
        ax.set_title(TXT["patient_vs_norm"], color="white", fontweight="bold")
        ax.legend(facecolor=DARK_AX, labelcolor="white")

        p = os.path.join(out_dir, "chart_norm.png")
        fig.tight_layout(); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
        paths["norm"] = p

    return paths


def generate_pdf(summary, trials, patient_id, age_group, chart_paths, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    fname    = os.path.join(out_dir, f"reporte_{patient_id}_{date_str}.pdf")

    doc    = SimpleDocTemplate(fname, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_s = ParagraphStyle("t",  fontSize=20, fontName="Helvetica-Bold",
                              textColor=colors.HexColor("#1a237e"),
                              alignment=TA_CENTER, spaceAfter=6)
    sub_s   = ParagraphStyle("s",  fontSize=11,
                              textColor=colors.HexColor("#455a64"),
                              alignment=TA_CENTER, spaceAfter=12)
    h2_s    = ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
                              textColor=colors.HexColor("#1a237e"), spaceBefore=14)
    body_s  = ParagraphStyle("b",  fontSize=10, leading=14)

    story = []
    grp   = AGE_GROUPS.get(age_group, {})

    story.append(Paragraph(TXT["title"], title_s))
    story.append(Paragraph(TXT["subtitle"], sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.3*cm))

    total_t  = len(trials)
    total_ok = sum(1 for t in trials if t["correct"])
    total_to = sum(1 for t in trials if t["timed_out"])
    all_rts  = [t["rt_ms"] for t in trials if not t["timed_out"]]
    mean_rt  = sum(all_rts)/len(all_rts) if all_rts else 0

    info = [
        [TXT["patient"],    patient_id,
         TXT["date"],       datetime.now().strftime("%d/%m/%Y %H:%M")],
        [TXT["age_group"],  grp.get("label", {}).get(LANGUAGE, age_group),
         TXT["trials"],     str(total_t)],
        [TXT["corrects"],   f"{total_ok} ({total_ok/max(total_t,1)*100:.1f}%)",
         TXT["timeouts"],   str(total_to)],
        [TXT["rt_global"],  f"{mean_rt:.0f} ms",
         TXT["norm_rt_inc"],f"{grp.get('norm_rt_incongruent','—')} ms"],
    ]
    tbl = Table(info, colWidths=[3.2*cm, 4.8*cm, 3.2*cm, 4.8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1), colors.HexColor("#e8eaf6")),
        ("BACKGROUND",(2,0),(2,-1), colors.HexColor("#e8eaf6")),
        ("FONTNAME",  (0,0),(-1,-1),"Helvetica"),
        ("FONTSIZE",  (0,0),(-1,-1), 9),
        ("GRID",      (0,0),(-1,-1), 0.5, colors.HexColor("#c5cae9")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,colors.HexColor("#f5f5f5")]),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── NUEVA SECCIÓN: LATERALIDAD ──
    story.append(Paragraph(TXT["lat_title"], h2_s))
    story.append(Spacer(1, 0.2*cm))
    
    # Las llaves deben coincidir con la data en español de MediaPipe que guardamos
    hand_stats = {"Derecha": {"n": 0, "ok": 0, "rts": []}, "Izquierda": {"n": 0, "ok": 0, "rts": []}}
    for t in trials:
        h = t.get("hand_used", "No detectada")
        if h in hand_stats:
            hand_stats[h]["n"] += 1
            if t["correct"]: hand_stats[h]["ok"] += 1
            if not t["timed_out"]: hand_stats[h]["rts"].append(t["rt_ms"])
    
    lat_rows = [[TXT["hand_used"], TXT["trials"], TXT["accuracy"], TXT["rt_avg"]]]
    lat_rt_means = {}
    for h_key in ["Derecha", "Izquierda"]:
        st = hand_stats[h_key]
        display_h = TXT["right"] if h_key == "Derecha" else TXT["left"]
        
        if st["n"] > 0:
            acc = (st["ok"] / st["n"]) * 100
            rt_mean = sum(st["rts"]) / len(st["rts"]) if st["rts"] else 0
            lat_rt_means[h_key] = rt_mean
            lat_rows.append([display_h, str(st["n"]), f"{acc:.1f}%", f"{rt_mean:.0f} ms"])
        else:
            lat_rows.append([display_h, "0", TXT["na"], TXT["na"]])
            lat_rt_means[h_key] = 0

    t_lat = Table(lat_rows, colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
    t_lat.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#006064")),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
        ("ALIGN",     (0,0),(-1,-1), "CENTER"),
        ("GRID",      (0,0),(-1,-1), 0.5, colors.HexColor("#b2ebf2")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#e0f7fa")]),
    ]))
    story.append(t_lat)
    story.append(Spacer(1, 0.4*cm))

    # Tabla de métricas Stroop clásicas
    story.append(Paragraph(TXT["stroop_title"], h2_s))
    story.append(Spacer(1, 0.2*cm))

    hdr = [TXT["level"], TXT["trials"], TXT["accuracy"], TXT["rt_avg"], TXT["std_rt"],
           TXT["interference"], TXT["tremor"], TXT["corrections"]]
    rows = [hdr]
    for lvl in sorted(summary.keys()):
        s = summary[lvl]
        rows.append([
            f"{TXT['level']} {lvl}",
            str(s["total"]),
            f"{s['accuracy_pct']}%",
            f"{s['mean_rt_ms']} ms",
            f"{s.get('std_rt_ms',0)} ms",
            f"{s['interference_ms']:+.0f} ms",
            f"{s['mean_tremor']:.4f}",
            f"{s['mean_corrections']:.2f}",
        ])
    t2 = Table(rows, colWidths=[3.0*cm,1.5*cm,1.8*cm,2.0*cm,
                                  1.8*cm,2.3*cm,1.8*cm,2.0*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 8),
        ("ALIGN",     (0,0),(-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),
         [colors.white, colors.HexColor("#f3f4ff")]),
        ("GRID",      (0,0),(-1,-1), 0.5, colors.HexColor("#c5cae9")),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # Gráficas
    story.append(Paragraph(TXT["visual_analysis"], h2_s))
    for key, lbl in [("norm", TXT["chart_norm"]),
                     ("rt", TXT["chart_rt"]),
                     ("accuracy", TXT["chart_acc"]),
                     ("learning", TXT["chart_learn"]),
                     ("motor", TXT["chart_motor"])]:
        p = chart_paths.get(key)
        if p and os.path.exists(p):
            story.append(Paragraph(lbl, body_s))
            story.append(RLImage(p, width=15*cm, height=6.5*cm))
            story.append(Spacer(1, 0.3*cm))

    # Observaciones
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#c5cae9")))
    story.append(Paragraph(TXT["obs_title"], h2_s))
    story.append(Spacer(1, 0.2*cm))

    obs = []
    norm_int = grp.get("norm_interference", 0)
    lvls     = sorted(summary.keys())

    # --- REGLA CLÍNICA DE LATERALIDAD ---
    if hand_stats["Derecha"]["n"] > 0 and hand_stats["Izquierda"]["n"] > 0:
        rt_diff = abs(lat_rt_means["Derecha"] - lat_rt_means["Izquierda"])
        if rt_diff > 300:
            lenta_key = "Derecha" if lat_rt_means["Derecha"] > lat_rt_means["Izquierda"] else "Izquierda"
            lenta_disp = TXT["right"] if lenta_key == "Derecha" else TXT["left"]
            obs.append(TXT["obs_asymmetry"].format(lenta=lenta_disp.lower(), rt_diff=rt_diff))

    if len(lvls) >= 2:
        rt1   = summary[lvls[0]]["mean_rt_ms"]
        rtL   = summary[lvls[-1]]["mean_rt_ms"]
        obs.append(TXT["obs_rt_inc"].format(diff=(rtL-rt1), lvl=lvls[-1], rt1=rt1, rtL=rtL))

    for lvl in lvls:
        s = summary[lvl]
        interf = s["interference_ms"]
        if lvl > 1 and abs(interf) > 0:
            flag = TXT["high"] if interf > norm_int * 1.3 else TXT["normal"]
            obs.append(TXT["obs_interf"].format(lvl=lvl, interf=interf, norm=norm_int, flag=flag))
        if s["accuracy_pct"] < 60:
            obs.append(TXT["obs_acc_low"].format(lvl=lvl, acc=s['accuracy_pct']))
        if s["mean_tremor"] > 0.05:
            obs.append(TXT["obs_tremor"].format(lvl=lvl, tremor=s['mean_tremor']))
        if s["timeouts"] > s["total"] * 0.3:
            obs.append(TXT["obs_timeout"].format(lvl=lvl, timeouts=s['timeouts']))

    if not obs:
        obs.append(TXT["obs_none"])
    obs.append(TXT["obs_disclaimer"])

    for line in obs:
        story.append(Paragraph(line, body_s))
        story.append(Spacer(1, 0.1*cm))

    doc.build(story)
    return fname


def generate_full_report(summary, trials, patient_id=PATIENT_ID,
                          age_group="young_adult"):
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(REPORTS_DIR, f"{patient_id}_{ts}")
    charts  = generate_charts(summary, trials, age_group, out_dir)
    pdf     = generate_pdf(summary, trials, patient_id, age_group, charts, out_dir)
    return pdf
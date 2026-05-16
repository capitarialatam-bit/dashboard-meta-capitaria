import re
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

DICCIONARIO = {
    "EP": "Evento presencial", "WE": "Webinar",    "AC": "Activación",
    "IN": "Informes",          "EB": "Ebook",       "BP": "Blog Post",
    "NT": "Nutrición",         "MC": "Masterclass", "WK": "Weekly",
    "DJ": "Dojo",              "BD": "Branding",    "PR": "Prensa",
    "CA": "Cápsulas orgánicas","LI": "LinkedIn Líderes", "EX": "Experimentos",
    "TF": "TOFU",              "MF": "MOFU",        "BF": "BOFU",
    "FL": "Flagship",
}


def _categoria(camp: str, dic_bb: str) -> str:
    if dic_bb and str(dic_bb) not in ("nan", "None", ""):
        return str(dic_bb)
    m = re.search(r'-([A-Z]{2})\d+', str(camp).upper())
    if m and m.group(1) in DICCIONARIO:
        return DICCIONARIO[m.group(1)]
    return "—"


def _badge(v, bg, color):
    return (f"<span style='background:{bg};color:{color};padding:2px 8px;"
            f"border-radius:4px;font-size:0.82rem;font-weight:600;'>{v}</span>")


def _pct_badge(pct):
    if pct >= 75:
        return _badge(f"{pct:.0f}%", "#0f2318", "#6dba8a")
    if pct >= 50:
        return _badge(f"{pct:.0f}%", "#2e2510", "#d4b06a")
    return _badge(f"{pct:.0f}%", "#2e1515", "#e08080")


def render_nuevos(df_meta: pd.DataFrame, df_nuevos: pd.DataFrame, pais: str):
    """
    df_meta   : resultado de get_resumen_por_pais (pais, gasto, leads)
    df_nuevos : resultado de leer_leads_nuevos (created_at, country, utm_medium, leads_nuevos)
    """
    # ── Agregar leads nuevos por país ────────────────────────────────────────
    if df_nuevos.empty:
        nuevos_display = {}
        nuevos_bau     = {}
    else:
        grp = df_nuevos.groupby(["country", "utm_medium"])["leads_nuevos"].sum()
        nuevos_display = grp.xs("display",     level="utm_medium").to_dict() if "display"     in grp.index.get_level_values("utm_medium") else {}
        nuevos_bau     = grp.xs("bau-display", level="utm_medium").to_dict() if "bau-display" in grp.index.get_level_values("utm_medium") else {}

    # ── Tabla resumen por país ───────────────────────────────────────────────
    paises = ["Chile", "Mexico", "Uruguay", "Peru"]
    meta_leads = df_meta.set_index("pais")["leads"].to_dict() if not df_meta.empty else {}

    filas_html = ""
    totales = {"meta": 0, "nuevos": 0, "bau": 0}

    for p in paises:
        meta    = int(meta_leads.get(p, 0))
        nuevos  = int(nuevos_display.get(p, 0))
        bau     = int(nuevos_bau.get(p, 0))
        total_n = nuevos + bau
        reingresos = max(meta - total_n, 0)
        pct = (total_n / meta * 100) if meta > 0 else 0

        totales["meta"]   += meta
        totales["nuevos"] += nuevos
        totales["bau"]    += bau

        highlight = "background:#1e1e1e;" if p == pais else ""
        filas_html += (
            f"<tr style='{highlight}'>"
            f"<td style='color:{'white' if p==pais else '#aaa'};font-weight:{'600' if p==pais else '400'};'>{p}</td>"
            f"<td style='text-align:center;color:white;font-weight:600;'>{meta:,}</td>"
            f"<td style='text-align:center;color:#6dba8a;'>{nuevos:,}</td>"
            f"<td style='text-align:center;color:#6aaad4;'>{bau:,}</td>"
            f"<td style='text-align:center;color:#d4b06a;'>{reingresos:,}</td>"
            f"<td style='text-align:center;'>{_pct_badge(pct)}</td>"
            f"</tr>"
        )

    total_meta   = totales["meta"]
    total_nuevos = totales["nuevos"] + totales["bau"]
    total_reing  = max(total_meta - total_nuevos, 0)
    total_pct    = (total_nuevos / total_meta * 100) if total_meta > 0 else 0

    filas_html += (
        f"<tr style='background:#2a2a2a;border-top:2px solid #444;'>"
        f"<td style='color:white;font-weight:700;'>TOTAL</td>"
        f"<td style='text-align:center;color:white;font-weight:700;'>{total_meta:,}</td>"
        f"<td style='text-align:center;color:#6dba8a;font-weight:700;'>{totales['nuevos']:,}</td>"
        f"<td style='text-align:center;color:#6aaad4;font-weight:700;'>{totales['bau']:,}</td>"
        f"<td style='text-align:center;color:#d4b06a;font-weight:700;'>{total_reing:,}</td>"
        f"<td style='text-align:center;'>{_pct_badge(total_pct)}</td>"
        f"</tr>"
    )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;font-family:sans-serif;}"
        ".t{width:100%;border-collapse:collapse;background:#161616;border-radius:10px;overflow:hidden;font-size:0.88rem;}"
        ".t thead tr{background:#2a2a2a;}"
        ".t th{color:#aaa;font-weight:500;padding:11px 14px;text-align:left;}"
        ".t th:not(:first-child){text-align:center;}"
        ".t td{color:#ccc;padding:10px 14px;border-top:1px solid #2a2a2a;}"
        ".t tbody tr:hover{filter:brightness(1.2);}"
        "</style>"
        "<table class='t'><thead><tr>"
        "<th>País</th>"
        "<th>Leads Meta</th>"
        "<th>Nuevos (Display)</th>"
        "<th>Nuevos (EP)</th>"
        "<th>Reingresos</th>"
        "<th>% Nuevos</th>"
        "</tr></thead><tbody>"
        f"{filas_html}"
        "</tbody></table>"
    )

    if df_nuevos.empty:
        st.info("Aún no hay datos cargados. Sube el Excel de Leads para ver esta tabla.")
    else:
        components.html(html, height=260, scrolling=False)

    # ── Leyenda ─────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.72rem;color:#666;margin-top:6px;display:flex;gap:16px;'>"
        "<span style='color:#6dba8a;'>● Nuevos Display</span>"
        "<span style='color:#6aaad4;'>● Nuevos EP (bau-display)</span>"
        "<span style='color:#d4b06a;'>● Reingresos</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Ranking de campañas por leads nuevos ────────────────────────────────
    if df_nuevos.empty:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Top campañas por Leads Nuevos")

    df_display = df_nuevos[df_nuevos["utm_medium"] == "display"].copy()
    df_display["categoria"] = df_display.apply(
        lambda r: _categoria(r["utm_campaign"], r.get("diccionario_bb", "")), axis=1
    )

    # Filtro de país
    paises_disponibles = sorted(df_display["country"].dropna().unique().tolist())
    opciones = ["Todos"] + paises_disponibles
    pais_ranking = st.selectbox("País", opciones, key="ranking_pais", label_visibility="collapsed")

    if pais_ranking != "Todos":
        df_display = df_display[df_display["country"] == pais_ranking]

    ranking = (
        df_display
        .groupby(["utm_campaign", "country", "categoria"])["leads_nuevos"]
        .sum()
        .reset_index()
        .sort_values("leads_nuevos", ascending=False)
        .head(15)
    )

    if ranking.empty:
        st.info("Sin datos de campañas para el período seleccionado.")
        return

    filas_r = ""
    for i, row in enumerate(ranking.itertuples(), 1):
        bar_w = int((row.leads_nuevos / ranking["leads_nuevos"].iloc[0]) * 100)
        dic = row.categoria
        filas_r += (
            f"<tr>"
            f"<td style='color:#666;text-align:center;'>{i}</td>"
            f"<td style='color:white;font-weight:500;'>{row.utm_campaign}</td>"
            f"<td style='color:#aaa;'>{dic}</td>"
            f"<td style='color:#aaa;font-size:0.8rem;'>{row.country}</td>"
            f"<td style='min-width:140px;'>"
            f"<div style='display:flex;align-items:center;gap:8px;'>"
            f"<div style='background:#6dba8a;height:6px;border-radius:3px;width:{bar_w}%;min-width:4px;'></div>"
            f"<span style='color:#6dba8a;font-weight:600;font-size:0.85rem;'>{int(row.leads_nuevos)}</span>"
            f"</div></td>"
            f"</tr>"
        )

    html_r = (
        "<style>"
        "body{margin:0;background:#0e1117;font-family:sans-serif;}"
        ".r{width:100%;border-collapse:collapse;background:#161616;border-radius:10px;overflow:hidden;font-size:0.85rem;}"
        ".r thead tr{background:#2a2a2a;}"
        ".r th{color:#aaa;font-weight:500;padding:10px 14px;text-align:left;}"
        ".r td{color:#ccc;padding:9px 14px;border-top:1px solid #222;}"
        ".r tbody tr:hover{filter:brightness(1.2);}"
        "</style>"
        "<table class='r'><thead><tr>"
        "<th style='width:40px;text-align:center;'>#</th>"
        "<th>Campaña</th>"
        "<th>Categoría</th>"
        "<th>País</th>"
        "<th>Leads Nuevos</th>"
        "</tr></thead><tbody>"
        f"{filas_r}"
        "</tbody></table>"
    )

    height_r = 50 + len(ranking) * 42
    components.html(html_r, height=min(height_r, 700), scrolling=True)

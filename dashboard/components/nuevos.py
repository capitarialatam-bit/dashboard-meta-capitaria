import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


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

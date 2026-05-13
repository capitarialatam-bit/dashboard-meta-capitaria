import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


def _es_evento_presencial(nombre: str) -> bool:
    return "-EP" in str(nombre).upper()


def _cell(v: str, bg: str, color: str) -> str:
    return (
        f"<span style='background:{bg};color:{color};padding:2px 7px;"
        f"border-radius:4px;font-weight:500;font-size:0.82rem;'>{v}</span>"
    )


def _badge_costo(v: float) -> str:
    if v == 0:
        return "<span style='color:#555;'>—</span>"
    if v > 15:
        return _cell(f"${v:.2f}", "#2e1515", "#e08080")
    if v >= 8:
        return _cell(f"${v:.2f}", "#2e2510", "#d4b06a")
    return _cell(f"${v:.2f}", "#0f2318", "#6dba8a")


def _badge_ctr(v: float) -> str:
    if v < 1:
        return _cell(f"{v:.2f}%", "#2e1515", "#e08080")
    if v < 1.5:
        return _cell(f"{v:.2f}%", "#2e2510", "#d4b06a")
    if v < 2.5:
        return _cell(f"{v:.2f}%", "#0f2318", "#6dba8a")
    return _cell(f"{v:.2f}%", "#102030", "#6aaad4")


def _badge_freq(v: float) -> str:
    if v > 2.5:
        return _cell(f"{v:.2f}", "#2e1515", "#e08080")
    if v >= 1.5:
        return _cell(f"{v:.2f}", "#2e2510", "#d4b06a")
    return _cell(f"{v:.2f}", "#0f2318", "#6dba8a")


def _badge_cpm(v: float) -> str:
    if v > 15:
        return _cell(f"${v:.2f}", "#2e1515", "#e08080")
    if v >= 10:
        return _cell(f"${v:.2f}", "#2e2510", "#d4b06a")
    return _cell(f"${v:.2f}", "#0f2318", "#6dba8a")


def _thumbnail(url: str) -> str:
    if str(url).startswith("http"):
        return (
            f"<img src='{url}' style='width:52px;height:52px;object-fit:cover;"
            f"border-radius:6px;border:1px solid #2e2e2e;' />"
        )
    return "<div style='width:52px;height:52px;background:#242424;border-radius:6px;border:1px solid #2e2e2e;'></div>"


def render_rendimiento(df: pd.DataFrame, pais: str):
    df_pais = df[df["pais"] == pais].copy() if not df.empty else df.copy()
    df_pais = df_pais[~df_pais["campana"].apply(_es_evento_presencial)]

    if df_pais.empty:
        st.info("Sin datos para este país en el rango seleccionado.")
        return

    df_sorted = df_pais.sort_values("leads", ascending=False).reset_index(drop=True)

    filas = ""
    for i, row in df_sorted.iterrows():
        filas += (
            f"<tr>"
            f"<td style='color:#666;'>{i+1}.</td>"
            f"<td>{_thumbnail(row['imagen'])}</td>"
            f"<td style='color:white;max-width:220px;'>"
            f"  <div style='font-size:0.82rem;'>{row['anuncio']}</div>"
            f"  <div style='color:#666;font-size:0.72rem;margin-top:2px;'>{row['campana']}</div>"
            f"</td>"
            f"<td style='color:white;text-align:center;font-weight:600;'>{int(row['leads'])}</td>"
            f"<td style='text-align:center;'>{_badge_costo(row['costo_lead'])}</td>"
            f"<td style='text-align:center;'>{_badge_ctr(row['ctr'])}</td>"
            f"<td style='text-align:center;'>{_badge_freq(row['frecuencia'])}</td>"
            f"<td style='text-align:center;'>{_badge_cpm(row['cpm'])}</td>"
            f"</tr>"
        )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;}"
        ".t{width:100%;border-collapse:collapse;background:#1e1e1e;border-radius:10px;overflow:hidden;"
        "font-size:0.85rem;font-family:sans-serif;}"
        ".t thead tr{background:#252525;}"
        ".t th{color:#888;font-weight:400;padding:10px 12px;text-align:left;font-size:0.8rem;}"
        ".t th.c{text-align:center;}"
        ".t td{color:white;padding:8px 12px;border-top:1px solid #252525;vertical-align:middle;}"
        ".t tbody tr:hover{background:#242424;}"
        "</style>"
        "<table class='t'><thead><tr>"
        "<th></th>"
        "<th>Creativo</th>"
        "<th>Anuncio / Campaña</th>"
        "<th class='c'>Leads</th>"
        "<th class='c'>Costo/resultado</th>"
        "<th class='c'>CTR único</th>"
        "<th class='c'>Frecuencia</th>"
        "<th class='c'>CPM</th>"
        "</tr></thead>"
        "<tbody>" + filas + "</tbody></table>"
    )

    st.markdown(
        "<div style='display:flex;gap:14px;margin-bottom:8px;font-size:0.72rem;color:#666;'>"
        "<span style='color:#6dba8a;'>● Bueno</span>"
        "<span style='color:#d4b06a;'>● Medio</span>"
        "<span style='color:#e08080;'>● Revisar</span>"
        "<span style='color:#6aaad4;'>● Excelente (CTR)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    height = 80 + len(df_sorted) * 70
    components.html(html, height=min(height, 700), scrolling=True)

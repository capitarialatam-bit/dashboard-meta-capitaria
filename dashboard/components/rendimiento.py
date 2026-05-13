import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


def _es_evento_presencial(nombre: str) -> bool:
    return "-EP" in str(nombre).upper()


def _badge_cpm(v: float) -> str:
    if v > 15:
        bg, color = "#3a0f0f", "#ff6b6b"
    elif v >= 10:
        bg, color = "#3a2a0a", "#ffd43b"
    else:
        bg, color = "#0d2b1a", "#69db7c"
    return f"<span style='background:{bg};color:{color};padding:3px 8px;border-radius:4px;font-weight:600;'>${v:.2f}</span>"


def _badge_ctr(v: float) -> str:
    if v < 1:
        bg, color = "#3a0f0f", "#ff6b6b"
    elif v < 1.5:
        bg, color = "#3a2a0a", "#ffd43b"
    elif v < 2.5:
        bg, color = "#0d2b1a", "#69db7c"
    else:
        bg, color = "#0d1f3a", "#74c0fc"
    return f"<span style='background:{bg};color:{color};padding:3px 8px;border-radius:4px;font-weight:600;'>{v:.2f}%</span>"


def _badge_costo(v: float) -> str:
    if v == 0:
        return "<span style='color:#666;'>—</span>"
    if v > 15:
        bg, color = "#3a0f0f", "#ff6b6b"
    elif v >= 8:
        bg, color = "#3a2a0a", "#ffd43b"
    else:
        bg, color = "#0d2b1a", "#69db7c"
    return f"<span style='background:{bg};color:{color};padding:3px 8px;border-radius:4px;font-weight:600;'>${v:.2f}</span>"


def _badge_freq(v: float) -> str:
    if v > 2.5:
        bg, color = "#3a0f0f", "#ff6b6b"
    elif v >= 1.5:
        bg, color = "#3a2a0a", "#ffd43b"
    else:
        bg, color = "#0d2b1a", "#69db7c"
    return f"<span style='background:{bg};color:{color};padding:3px 8px;border-radius:4px;font-weight:600;'>{v:.2f}</span>"


def _thumbnail(url: str) -> str:
    if str(url).startswith("http"):
        return (
            f"<img src='{url}' style='width:56px;height:56px;object-fit:cover;"
            f"border-radius:6px;border:1px solid #333;' />"
        )
    return "<div style='width:56px;height:56px;background:#2a2a2a;border-radius:6px;border:1px solid #333;'></div>"


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
            f"<td style='color:#888;'>{i+1}.</td>"
            f"<td>{_thumbnail(row['imagen'])}</td>"
            f"<td style='color:white;max-width:220px;'>"
            f"  <div style='font-size:0.82rem;'>{row['anuncio']}</div>"
            f"  <div style='color:#888;font-size:0.72rem;margin-top:2px;'>{row['campana']}</div>"
            f"</td>"
            f"<td style='color:white;text-align:center;'>{int(row['leads'])}</td>"
            f"<td style='text-align:center;'>{_badge_costo(row['costo_lead'])}</td>"
            f"<td style='text-align:center;'>{_badge_cpm(row['cpm'])}</td>"
            f"<td style='text-align:center;'>{_badge_ctr(row['ctr'])}</td>"
            f"<td style='text-align:center;'>{_badge_freq(row['frecuencia'])}</td>"
            f"</tr>"
        )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;}"
        ".t{width:100%;border-collapse:collapse;background:#1e1e1e;border-radius:10px;overflow:hidden;font-size:0.85rem;font-family:sans-serif;}"
        ".t thead tr{background:#2a2a2a;}"
        ".t th{color:#aaa;font-weight:500;padding:10px 12px;text-align:left;}"
        ".t th.center{text-align:center;}"
        ".t td{color:white;padding:8px 12px;border-top:1px solid #2a2a2a;vertical-align:middle;}"
        ".t tbody tr:hover{filter:brightness(1.12);}"
        "</style>"
        "<table class='t'><thead><tr>"
        "<th></th>"
        "<th>Creativo</th>"
        "<th>Anuncio / Campaña</th>"
        "<th class='center'>Leads</th>"
        "<th class='center'>Costo/resultado</th>"
        "<th class='center'>CPM</th>"
        "<th class='center'>CTR único</th>"
        "<th class='center'>Frecuencia</th>"
        "</tr></thead>"
        "<tbody>" + filas + "</tbody></table>"
    )

    # Leyenda de colores
    st.markdown(
        "<div style='display:flex;gap:16px;margin-bottom:10px;font-size:0.75rem;'>"
        "<span style='color:#69db7c;'>● Bueno</span>"
        "<span style='color:#ffd43b;'>● Medio</span>"
        "<span style='color:#ff6b6b;'>● Revisar</span>"
        "<span style='color:#74c0fc;'>● Excelente (CTR)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    height = 80 + len(df_sorted) * 72
    components.html(html, height=min(height, 700), scrolling=True)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


def _es_ep(nombre: str) -> bool:
    return "-EP" in str(nombre).upper()


def _badge(v: str, bg: str, color: str) -> str:
    return (f"<span style='background:{bg};color:{color};padding:2px 7px;"
            f"border-radius:4px;font-weight:500;font-size:0.8rem;'>{v}</span>")


def _costo(v):
    if v == 0: return "<span style='color:#444;'>—</span>"
    if v > 15:  return _badge(f"${v:.2f}", "#2e1515", "#e08080")
    if v >= 8:  return _badge(f"${v:.2f}", "#2e2510", "#d4b06a")
    return _badge(f"${v:.2f}", "#0f2318", "#6dba8a")

def _ctr(v):
    if v < 1:   return _badge(f"{v:.2f}%", "#2e1515", "#e08080")
    if v < 1.5: return _badge(f"{v:.2f}%", "#2e2510", "#d4b06a")
    if v < 2.5: return _badge(f"{v:.2f}%", "#0f2318", "#6dba8a")
    return _badge(f"{v:.2f}%", "#102030", "#6aaad4")

def _freq(v):
    if v > 2.5: return _badge(f"{v:.2f}", "#2e1515", "#e08080")
    if v >= 1.5:return _badge(f"{v:.2f}", "#2e2510", "#d4b06a")
    return _badge(f"{v:.2f}", "#0f2318", "#6dba8a")

def _cpm(v):
    if v > 15:  return _badge(f"${v:.2f}", "#2e1515", "#e08080")
    if v >= 10: return _badge(f"${v:.2f}", "#2e2510", "#d4b06a")
    return _badge(f"${v:.2f}", "#0f2318", "#6dba8a")

def _thumb(url):
    if str(url).startswith("http"):
        return (f"<img src='{url}' style='width:48px;height:48px;object-fit:cover;"
                f"border-radius:5px;border:1px solid #2e2e2e;vertical-align:middle;'>")
    return "<div style='width:48px;height:48px;background:#222;border-radius:5px;display:inline-block;vertical-align:middle;'></div>"

def _metrics_inline(leads, costo, ctr, freq, cpm):
    return (f"<span style='color:#aaa;font-size:0.78rem;margin-left:16px;'>"
            f"<b style='color:white;'>{int(leads)}</b> leads &nbsp;·&nbsp; "
            f"{_costo(costo)} &nbsp;·&nbsp; {_ctr(ctr)} &nbsp;·&nbsp; "
            f"{_freq(freq)} &nbsp;·&nbsp; {_cpm(cpm)}</span>")


def _agg_metrics(rows):
    leads = rows["leads"].sum()
    gasto = rows["gasto"].sum() if "gasto" in rows.columns else 0
    imp   = rows["impresiones"].sum() if "impresiones" in rows.columns else 0
    alc   = rows["alcance"].sum() if "alcance" in rows.columns else 0
    ctr_p = rows["ctr_pond"].sum() if "ctr_pond" in rows.columns else 0
    costo = gasto / leads if leads > 0 else 0
    cpm   = (gasto / imp) * 1000 if imp > 0 else rows["cpm"].mean() if "cpm" in rows.columns else 0
    ctr   = ctr_p / imp if imp > 0 else rows["ctr"].mean() if "ctr" in rows.columns else 0
    freq  = imp / alc if alc > 0 else rows["frecuencia"].mean() if "frecuencia" in rows.columns else 0
    return leads, costo, ctr, freq, cpm


def render_rendimiento(df: pd.DataFrame, pais: str):
    df_pais = df[df["pais"] == pais].copy() if not df.empty else df.copy()
    df_pais = df_pais[~df_pais["campana"].apply(_es_ep)]

    if df_pais.empty:
        st.info("Sin datos para este país en el rango seleccionado.")
        return

    # ── Encabezado de columnas ──────────────────────────────────────────────
    header = (
        "<div style='display:grid;grid-template-columns:1fr 80px 110px 90px 80px 90px;"
        "gap:0;background:#252525;padding:8px 14px;border-radius:8px 8px 0 0;"
        "font-size:0.75rem;color:#777;font-weight:400;'>"
        "<span>Anuncio / Conjunto / Campaña</span>"
        "<span style='text-align:center;'>Leads</span>"
        "<span style='text-align:center;'>Costo/res.</span>"
        "<span style='text-align:center;'>CTR único</span>"
        "<span style='text-align:center;'>Frecuencia</span>"
        "<span style='text-align:center;'>CPM</span>"
        "</div>"
    )

    bloques = ""
    campanas = df_pais["campana"].unique()
    campanas_sorted = sorted(campanas, key=lambda c: df_pais[df_pais["campana"] == c]["leads"].sum(), reverse=True)

    for campana in campanas_sorted:
        df_camp = df_pais[df_pais["campana"] == campana]
        cl, cc, cctr, cf, ccpm = _agg_metrics(df_camp)

        adsets_html = ""
        adsets = df_camp["adset"].unique()
        adsets_sorted = sorted(adsets, key=lambda a: df_camp[df_camp["adset"] == a]["leads"].sum(), reverse=True)

        for adset in adsets_sorted:
            df_adset = df_camp[df_camp["adset"] == adset]
            al, ac, actr, af, acpm = _agg_metrics(df_adset)

            ads_html = ""
            for _, row in df_adset.sort_values("leads", ascending=False).iterrows():
                ads_html += (
                    f"<div style='display:grid;grid-template-columns:1fr 80px 110px 90px 80px 90px;"
                    f"gap:0;padding:8px 14px 8px 56px;border-top:1px solid #232323;"
                    f"background:#191919;align-items:center;'>"
                    f"<span style='display:flex;align-items:center;gap:10px;'>"
                    f"{_thumb(row['imagen'])}"
                    f"<span style='color:#ccc;font-size:0.8rem;'>{row['anuncio']}</span></span>"
                    f"<span style='text-align:center;color:white;font-weight:600;font-size:0.82rem;'>{int(row['leads'])}</span>"
                    f"<span style='text-align:center;'>{_costo(row['costo_lead'])}</span>"
                    f"<span style='text-align:center;'>{_ctr(row['ctr'])}</span>"
                    f"<span style='text-align:center;'>{_freq(row['frecuencia'])}</span>"
                    f"<span style='text-align:center;'>{_cpm(row['cpm'])}</span>"
                    f"</div>"
                )

            adsets_html += (
                f"<details style='border-top:1px solid #2a2a2a;'>"
                f"<summary style='display:grid;grid-template-columns:1fr 80px 110px 90px 80px 90px;"
                f"gap:0;padding:8px 14px 8px 28px;background:#1e1e1e;cursor:pointer;"
                f"list-style:none;align-items:center;'>"
                f"<span style='color:#aaa;font-size:0.8rem;'>▸ {adset}</span>"
                f"<span style='text-align:center;color:white;font-weight:600;font-size:0.82rem;'>{int(al)}</span>"
                f"<span style='text-align:center;'>{_costo(ac)}</span>"
                f"<span style='text-align:center;'>{_ctr(actr)}</span>"
                f"<span style='text-align:center;'>{_freq(af)}</span>"
                f"<span style='text-align:center;'>{_cpm(acpm)}</span>"
                f"</summary>"
                f"{ads_html}"
                f"</details>"
            )

        bloques += (
            f"<details style='border-top:1px solid #333;'>"
            f"<summary style='display:grid;grid-template-columns:1fr 80px 110px 90px 80px 90px;"
            f"gap:0;padding:10px 14px;background:#242424;cursor:pointer;"
            f"list-style:none;align-items:center;'>"
            f"<span style='color:white;font-size:0.85rem;font-weight:500;'>▸ {campana}</span>"
            f"<span style='text-align:center;color:white;font-weight:700;font-size:0.85rem;'>{int(cl)}</span>"
            f"<span style='text-align:center;'>{_costo(cc)}</span>"
            f"<span style='text-align:center;'>{_ctr(cctr)}</span>"
            f"<span style='text-align:center;'>{_freq(cf)}</span>"
            f"<span style='text-align:center;'>{_cpm(ccpm)}</span>"
            f"</summary>"
            f"{adsets_html}"
            f"</details>"
        )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;font-family:sans-serif;}"
        "details>summary::-webkit-details-marker{display:none;}"
        "details[open]>summary span:first-child{opacity:1;}"
        "details summary:hover{filter:brightness(1.15);}"
        "</style>"
        f"{header}"
        f"<div style='border:1px solid #333;border-top:none;border-radius:0 0 8px 8px;overflow:hidden;'>"
        f"{bloques}"
        f"</div>"
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

    n_ads = len(df_pais)
    height = 60 + len(campanas_sorted) * 44 + n_ads * 65
    components.html(html, height=min(height, 750), scrolling=True)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from data.campaign_categories import categoria_de_campania

COLOR_HOMBRES = "#6aaad4"
COLOR_MUJERES = "#d4b06a"
COLOR_OTROS   = "#888888"

SORT_OPTIONS = {
    "Importe gastado (desc.)": ("gasto_total", False),
    "Categoría":               ("categoria", True),
    "Campaña":                 ("campana", True),
    "Leads hombres":           ("leads_h", False),
    "% hombres":               ("pct_h", False),
    "CPL hombres":             ("cpl_h", True),
    "Leads mujeres":           ("leads_m", False),
    "% mujeres":               ("pct_m", False),
    "CPL mujeres":             ("cpl_m", True),
    "Total Leads":             ("leads_total", False),
    "CPL Total":               ("cpl_total", True),
}


def _money(v) -> str:
    return f"${v:,.2f}"


def _cpl(gasto: float, leads: float):
    """Devuelve el CPL como float, o None si no hay leads (para no dividir por 0)."""
    return (gasto / leads) if leads > 0 else None


def _cpl_str(cpl) -> str:
    return "—" if cpl is None or pd.isna(cpl) else f"${cpl:,.2f}"


def _pct(parte: float, total: float) -> float:
    return (parte / total * 100) if total > 0 else 0.0


def _agregar_por_campania(df_pais: pd.DataFrame) -> pd.DataFrame:
    """Consolida por campaign_id+campaña y separa gasto/leads por género.
    'otros' agrupa cualquier valor que no sea exactamente 'male'/'female'
    (ej. 'unknown') — nunca se mezcla con hombres o mujeres."""
    filas = []
    for (campaign_id, campana), grupo in df_pais.groupby(["campaign_id", "campana"]):
        es_h = grupo["gender"] == "male"
        es_m = grupo["gender"] == "female"
        es_o = ~es_h & ~es_m

        gasto_h, leads_h = grupo.loc[es_h, "gasto"].sum(), grupo.loc[es_h, "leads"].sum()
        gasto_m, leads_m = grupo.loc[es_m, "gasto"].sum(), grupo.loc[es_m, "leads"].sum()
        gasto_o, leads_o = grupo.loc[es_o, "gasto"].sum(), grupo.loc[es_o, "leads"].sum()

        gasto_total = gasto_h + gasto_m + gasto_o
        leads_total = leads_h + leads_m + leads_o

        filas.append({
            "campaign_id": campaign_id,
            "campana":     campana,
            "categoria":   categoria_de_campania(campana),
            "gasto_h": gasto_h, "leads_h": leads_h,
            "gasto_m": gasto_m, "leads_m": leads_m,
            "gasto_o": gasto_o, "leads_o": leads_o,
            "gasto_total": gasto_total, "leads_total": leads_total,
            "pct_h": _pct(leads_h, leads_total),
            "pct_m": _pct(leads_m, leads_total),
            "pct_o": _pct(leads_o, leads_total),
            "cpl_h": _cpl(gasto_h, leads_h),
            "cpl_m": _cpl(gasto_m, leads_m),
            "cpl_total": _cpl(gasto_total, leads_total),
        })
    return pd.DataFrame(filas)


def render_campanas_genero(df: pd.DataFrame, pais: str):
    """
    df   : resultado de get_campanas_genero (columnas pais, campaign_id, campana,
           gender, gasto, leads) — ya consolidado por campaign_id en el connector.
    pais : 'Todos' o una clave de config.PAISES (Chile/Mexico/Peru/Uruguay).
    """
    COLS_REQUERIDAS = {"pais", "campaign_id", "campana", "gender", "gasto", "leads"}
    tiene_datos = not df.empty and COLS_REQUERIDAS.issubset(df.columns)

    if not tiene_datos:
        st.info("No hay datos de género disponibles para el período seleccionado.")
        return

    df_pais = df if pais == "Todos" else df[df["pais"] == pais]
    if df_pais.empty:
        st.info("No hay datos de género disponibles para el período seleccionado.")
        return

    df_agg = _agregar_por_campania(df_pais)
    if df_agg.empty:
        st.info("No hay datos de género disponibles para el período seleccionado.")
        return

    # ── Totales del período filtrado ────────────────────────────────────────
    gasto_total   = df_agg["gasto_total"].sum()
    leads_total   = int(df_agg["leads_total"].sum())
    gasto_h_tot   = df_agg["gasto_h"].sum()
    leads_h_tot   = int(df_agg["leads_h"].sum())
    gasto_m_tot   = df_agg["gasto_m"].sum()
    leads_m_tot   = int(df_agg["leads_m"].sum())
    leads_o_tot   = int(df_agg["leads_o"].sum())
    gasto_o_tot   = df_agg["gasto_o"].sum()

    pct_h_tot = _pct(leads_h_tot, leads_total)
    pct_m_tot = _pct(leads_m_tot, leads_total)
    pct_o_tot = _pct(leads_o_tot, leads_total)
    cpl_h_tot = _cpl(gasto_h_tot, leads_h_tot)
    cpl_m_tot = _cpl(gasto_m_tot, leads_m_tot)

    hay_otros = leads_o_tot > 0 or gasto_o_tot > 0

    # ── KPI cards ─────────────────────────────────────────────────────────────
    def _card(col, label, valor, sub=None, color="white"):
        with col:
            st.markdown(
                f"""
                <div style="background:#1e1e1e;border-radius:8px;padding:14px;margin-bottom:8px;">
                    <div style="color:#aaa;font-size:0.72rem;">{label}</div>
                    <div style="color:{color};font-size:1.3rem;font-weight:700;margin-top:4px;">{valor}</div>
                    {f"<div style='color:#888;font-size:0.7rem;margin-top:2px;'>{sub}</div>" if sub else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

    cols = st.columns(6)
    _card(cols[0], "Total invertido", _money(gasto_total))
    _card(cols[1], "Total leads", f"{leads_total:,}")
    _card(cols[2], "Leads hombres", f"{leads_h_tot:,}", f"{pct_h_tot:.0f}%", COLOR_HOMBRES)
    _card(cols[3], "Leads mujeres", f"{leads_m_tot:,}", f"{pct_m_tot:.0f}%", COLOR_MUJERES)
    _card(cols[4], "CPL hombres", _cpl_str(cpl_h_tot), color=COLOR_HOMBRES)
    _card(cols[5], "CPL mujeres", _cpl_str(cpl_m_tot), color=COLOR_MUJERES)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Distribución de leads por género ────────────────────────────────────
    st.markdown(
        "<div style='color:#aaa;font-size:0.8rem;margin-bottom:6px;'>Distribución de leads por género</div>",
        unsafe_allow_html=True,
    )
    segmentos = (
        f"<div style='background:{COLOR_HOMBRES};width:{pct_h_tot}%;'></div>"
        f"<div style='background:{COLOR_MUJERES};width:{pct_m_tot}%;'></div>"
        + (f"<div style='background:{COLOR_OTROS};width:{pct_o_tot}%;'></div>" if hay_otros else "")
    )
    leyenda = (
        f"<span style='color:{COLOR_HOMBRES};'>● Hombres {pct_h_tot:.0f}%</span>"
        f"<span style='color:{COLOR_MUJERES};'>● Mujeres {pct_m_tot:.0f}%</span>"
        + (f"<span style='color:{COLOR_OTROS};'>● Otros / Sin identificar {pct_o_tot:.0f}%</span>" if hay_otros else "")
    )
    st.markdown(
        f"""
        <div style="background:#1e1e1e;border-radius:8px;padding:14px;margin-bottom:8px;">
            <div style="display:flex;width:100%;height:10px;border-radius:5px;overflow:hidden;background:#333;">
                {segmentos}
            </div>
            <div style="display:flex;gap:16px;margin-top:8px;font-size:0.75rem;">
                {leyenda}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Insight automático (solo cálculos, sin IA) ──────────────────────────
    insights = []
    if leads_total > 0 and leads_h_tot != leads_m_tot:
        genero_mayor = "hombres" if leads_h_tot > leads_m_tot else "mujeres"
        pct_mayor = pct_h_tot if leads_h_tot > leads_m_tot else pct_m_tot
        insights.append(("Mayor volumen", f"Los {genero_mayor} representan el {pct_mayor:.0f}% de los leads del período."))

    if cpl_h_tot is not None and cpl_m_tot is not None and cpl_h_tot != cpl_m_tot:
        if cpl_h_tot < cpl_m_tot:
            genero_barato, genero_caro, cpl_barato, cpl_caro = "hombres", "mujeres", cpl_h_tot, cpl_m_tot
        else:
            genero_barato, genero_caro, cpl_barato, cpl_caro = "mujeres", "hombres", cpl_m_tot, cpl_h_tot
        diff_pct = (cpl_caro - cpl_barato) / cpl_caro * 100
        insights.append((
            "Diferencia de CPL",
            f"Los {genero_barato} cuestan {diff_pct:.0f}% menos por lead que los {genero_caro} "
            f"({_cpl_str(cpl_barato)} vs {_cpl_str(cpl_caro)}).",
        ))

    if insights:
        insight_html = "".join(
            f"<div style='margin-bottom:{8 if i < len(insights)-1 else 0}px;'>"
            f"<span style='color:#6dba8a;font-weight:600;font-size:0.8rem;'>{titulo}</span><br>"
            f"<span style='color:#ccc;font-size:0.85rem;'>{texto}</span></div>"
            for i, (titulo, texto) in enumerate(insights)
        )
        st.markdown(
            f"""
            <div style="background:#1e1e1e;border-radius:8px;padding:14px;margin-bottom:8px;border-left:3px solid #6dba8a;">
                {insight_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Orden de la tabla ────────────────────────────────────────────────────
    col_sort, col_dir, _ = st.columns([2, 1, 2])
    with col_sort:
        criterio = st.selectbox(
            "Ordenar por", list(SORT_OPTIONS.keys()),
            index=0, key="genero_sort_campo", label_visibility="collapsed",
        )
    campo, ascendente_default = SORT_OPTIONS[criterio]
    with col_dir:
        direccion = st.selectbox(
            "Dirección", ["Descendente", "Ascendente"],
            index=1 if ascendente_default else 0,
            key="genero_sort_dir", label_visibility="collapsed",
        )

    ascendente = (direccion == "Ascendente")
    df_sorted = df_agg.sort_values(campo, ascending=ascendente, na_position="last").reset_index(drop=True)

    # Nombres duplicados (mismo código de campaña, distinto campaign_id) →
    # mostrar ID para distinguirlos, igual que en Campañas por país.
    nombres_duplicados = set(
        df_agg[df_agg.duplicated(subset=["campana"], keep=False)]["campana"].unique()
    )

    # ── Tabla ─────────────────────────────────────────────────────────────────
    filas = ""
    for i, row in df_sorted.iterrows():
        otros_cell = (
            f"<td style='color:{COLOR_OTROS};font-size:0.8rem;'>{int(row['leads_o'])} · {row['pct_o']:.0f}%</td>"
            if hay_otros else ""
        )
        id_badge = ""
        if row["campana"] in nombres_duplicados:
            cid = str(row["campaign_id"])
            id_badge = (
                f" <span style='background:#1a2a3a;color:#6aaad4;font-size:0.65rem;"
                f"padding:2px 6px;border-radius:4px;font-weight:600;'>ID …{cid[-6:]}</span>"
            )
        filas += (
            f"<tr>"
            f"<td style='color:#888;'>{i+1}.</td>"
            f"<td style='color:#aaa;font-size:0.82rem;'>{row['categoria']}</td>"
            f"<td style='color:white;'>{row['campana']}{id_badge}</td>"
            f"<td style='color:white;'>{_money(row['gasto_total'])}</td>"
            f"<td style='color:{COLOR_HOMBRES};'>{int(row['leads_h'])} · {row['pct_h']:.0f}%"
            f"<br><span style='color:#777;font-size:0.72rem;'>CPL {_cpl_str(row['cpl_h'])}</span></td>"
            f"<td style='color:{COLOR_MUJERES};'>{int(row['leads_m'])} · {row['pct_m']:.0f}%"
            f"<br><span style='color:#777;font-size:0.72rem;'>CPL {_cpl_str(row['cpl_m'])}</span></td>"
            f"{otros_cell}"
            f"<td style='color:white;font-weight:600;'>{int(row['leads_total'])}</td>"
            f"<td style='color:white;'>{_cpl_str(row['cpl_total'])}</td>"
            f"</tr>"
        )

    otros_th = "<th>Otros</th>" if hay_otros else ""
    html = (
        "<style>"
        "body{margin:0;background:#0e1117;}"
        ".t{width:100%;border-collapse:collapse;background:#1e1e1e;border-radius:10px;overflow:hidden;font-size:0.85rem;font-family:sans-serif;}"
        ".t thead tr{background:#2a2a2a;}"
        ".t th{color:#aaa;font-weight:500;padding:11px 12px;text-align:left;white-space:nowrap;}"
        ".t td{color:white;padding:9px 12px;border-top:1px solid #2a2a2a;vertical-align:top;}"
        ".t tbody tr:hover{filter:brightness(1.15);}"
        "</style>"
        "<table class='t'>"
        "<thead><tr>"
        "<th></th>"
        "<th>Categoría</th>"
        "<th>Campaña</th>"
        "<th>Gastado</th>"
        "<th>Hombres</th>"
        "<th>Mujeres</th>"
        f"{otros_th}"
        "<th>Total Leads</th>"
        "<th>CPL Total</th>"
        "</tr></thead>"
        "<tbody>" + filas + "</tbody>"
        "</table>"
    )

    height = 60 + len(df_sorted) * 52
    components.html(html, height=min(height, 650), scrolling=True)

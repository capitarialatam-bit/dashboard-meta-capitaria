import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from config import PAISES


def _es_evento_presencial(nombre: str) -> bool:
    return "-EP" in str(nombre).upper()


def render_campanas(df: pd.DataFrame, pais: str):
    COLS_REQUERIDAS = {"pais", "campana", "gasto", "leads", "costo_lead"}
    tiene_datos = not df.empty and COLS_REQUERIDAS.issubset(df.columns)

    df_pais = df[df["pais"] == pais].copy() if tiene_datos else pd.DataFrame(columns=list(COLS_REQUERIDAS))

    # Separar EP del conteo general
    if not df_pais.empty:
        df_normales = df_pais[~df_pais["campana"].apply(_es_evento_presencial)]
    else:
        df_normales = df_pais

    gasto_total = df_normales["gasto"].sum() if not df_normales.empty else 0.0
    leads_total = int(df_normales["leads"].sum()) if not df_normales.empty else 0

    # Detectar nombres duplicados para mostrar ID en esos casos
    nombres_duplicados = set(
        df_pais[df_pais.duplicated(subset=["campana"], keep=False)]["campana"].unique()
    ) if "campaign_id" in df_pais.columns and not df_pais.empty else set()

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.markdown(
            f"""
            <div style="background:#1e1e1e;border-radius:8px;padding:14px;margin-bottom:8px;">
                <div style="color:#aaa;font-size:0.78rem;">Gasto {pais}</div>
                <div style="color:#aaa;font-size:0.7rem;margin-top:4px;">Importe gastado</div>
                <div style="color:white;font-size:1.5rem;font-weight:700;">${gasto_total:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background:#1e1e1e;border-radius:8px;padding:14px;margin-bottom:8px;">
                <div style="color:#aaa;font-size:0.78rem;">Total Leads</div>
                <div style="color:#aaa;font-size:0.7rem;margin-top:4px;">Excluye eventos presenciales</div>
                <div style="color:white;font-size:1.5rem;font-weight:700;">{leads_total}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if df_pais.empty:
        st.info("Sin datos para este país en el rango seleccionado.")
        return

    df_sorted = df_pais.sort_values("gasto", ascending=False).reset_index(drop=True)

    # ── Tabla ─────────────────────────────────────────────────────────────────
    filas = ""
    for i, row in df_sorted.iterrows():
        es_ep = _es_evento_presencial(row["campana"])
        costo = f"${row['costo_lead']:,.2f}" if row["costo_lead"] > 0 else "$0"

        # Badge EP
        ep_badge = (
            " <span style='background:#555;color:#ccc;font-size:0.65rem;"
            "padding:2px 6px;border-radius:4px;font-weight:600;'>EP</span>"
            if es_ep else ""
        )

        # Badge ID cuando el nombre está duplicado
        cid = str(row.get("campaign_id", ""))
        id_badge = ""
        if row["campana"] in nombres_duplicados and cid:
            id_badge = (
                f" <span style='background:#1a2a3a;color:#6aaad4;font-size:0.65rem;"
                f"padding:2px 6px;border-radius:4px;font-weight:600;'>ID …{cid[-6:]}</span>"
            )

        if es_ep:
            fila_style = "background:#2e2e2e;"
            nombre_cell = f"{row['campana']}{ep_badge}{id_badge}"
            color_texto = "color:#aaa;"
        else:
            fila_style = ""
            nombre_cell = f"{row['campana']}{ep_badge}{id_badge}"
            color_texto = "color:white;"

        filas += (
            f"<tr style='{fila_style}'>"
            f"<td style='color:#888;'>{i+1}.</td>"
            f"<td style='{color_texto}'>{nombre_cell}</td>"
            f"<td style='{color_texto}'>${row['gasto']:,.2f}</td>"
            f"<td style='{color_texto}'>{costo}</td>"
            f"<td style='{color_texto}'>{int(row['leads'])}</td>"
            f"</tr>"
        )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;}"
        ".t{width:100%;border-collapse:collapse;background:#1e1e1e;border-radius:10px;overflow:hidden;font-size:0.88rem;font-family:sans-serif;}"
        ".t thead tr{background:#2a2a2a;}"
        ".t th{color:#aaa;font-weight:500;padding:11px 14px;text-align:left;}"
        ".t td{color:white;padding:10px 14px;border-top:1px solid #2a2a2a;}"
        ".t tbody tr:hover{filter:brightness(1.15);}"
        "</style>"
        "<table class='t'>"
        "<thead><tr>"
        "<th></th>"
        "<th>Nombre campaña</th>"
        "<th>Importe gastado</th>"
        "<th>Coste por lead</th>"
        "<th>Leads</th>"
        "</tr></thead>"
        "<tbody>" + filas + "</tbody>"
        "</table>"
    )

    height = 60 + len(df_sorted) * 42
    components.html(html, height=min(height, 600), scrolling=True)

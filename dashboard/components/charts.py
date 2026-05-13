import calendar
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date
from config import PAISES, COLOR_VERDE, COLOR_ROJO


def _presupuesto_diario(presupuesto_mensual: float, fecha: date) -> float:
    dias_mes = calendar.monthrange(fecha.year, fecha.month)[1]
    return presupuesto_mensual / dias_mes


def _color_card(gasto: float, presupuesto: float) -> str:
    return COLOR_VERDE if gasto <= presupuesto else COLOR_ROJO


def render_kpi_cards(df_resumen: pd.DataFrame, fecha_ref: date):
    datos = {row["pais"]: row for _, row in df_resumen.iterrows()}
    cols = st.columns(len(PAISES))

    for col, (pais, config) in zip(cols, PAISES.items()):
        gasto = float(datos.get(pais, {}).get("gasto", 0.0))
        leads = int(datos.get(pais, {}).get("leads", 0))
        presupuesto_mensual = config["presupuesto_mensual"]
        p_diario = _presupuesto_diario(presupuesto_mensual, fecha_ref)
        color = _color_card(gasto, p_diario)

        with col:
            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom:8px;">
                    <div style="background:{color};border-radius:8px;padding:10px 8px 8px 8px;margin-bottom:6px;">
                        <div style="color:rgba(255,255,255,0.75);font-size:0.72rem;margin-bottom:2px;">
                            Gasto máximo diario
                        </div>
                        <span style="font-size:2rem;font-weight:700;color:white;">
                            {p_diario:,.0f}
                        </span>
                    </div>
                    <div style="color:#ccc;font-size:0.95rem;margin-bottom:8px;">Gasto {pais}</div>
                    <div style="background:#1e1e1e;border-radius:8px;padding:10px;margin-bottom:6px;">
                        <div style="color:#aaa;font-size:0.75rem;">Importe gastado</div>
                        <div style="color:white;font-size:1.3rem;font-weight:600;">${gasto:,.2f}</div>
                    </div>
                    <div style="background:#1e1e1e;border-radius:8px;padding:10px;">
                        <div style="color:#aaa;font-size:0.75rem;">Leads</div>
                        <div style="color:white;font-size:2rem;font-weight:700;">{leads}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_tabla_mensual(df_resumen: pd.DataFrame, fecha_ref: date):
    filas = ""
    for pais, config in PAISES.items():
        gasto = float(df_resumen[df_resumen["pais"] == pais]["gasto"].sum()) if not df_resumen.empty else 0.0
        pm = config["presupuesto_mensual"]
        pct = (gasto / pm * 100) if pm > 0 else 0.0
        filas += (
            "<tr>"
            f"<td>{pais}</td>"
            f"<td>${pm:,.2f}</td>"
            f"<td>${gasto:,.2f}</td>"
            f"<td>{pct:.2f}%</td>"
            "</tr>"
        )

    html = (
        "<style>"
        "body{margin:0;background:#0e1117;}"
        ".t{width:100%;border-collapse:collapse;background:#1e1e1e;border-radius:10px;overflow:hidden;font-size:0.9rem;font-family:sans-serif;}"
        ".t thead tr{background:#2a2a2a;}"
        ".t th{color:#aaa;font-weight:500;padding:12px 16px;text-align:left;}"
        ".t td{color:white;padding:11px 16px;border-top:1px solid #2a2a2a;}"
        ".t tbody tr:hover{background:#252525;}"
        "</style>"
        "<table class='t'>"
        "<thead><tr>"
        "<th>País por Campaña</th>"
        "<th>Presupuesto País</th>"
        "<th>Importe gastado</th>"
        "<th>% Ejecución</th>"
        "</tr></thead>"
        "<tbody>" + filas + "</tbody>"
        "</table>"
    )

    components.html(html, height=220, scrolling=False)

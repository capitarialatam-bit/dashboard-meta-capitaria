# Dashboard Meta Ads Capitaria — Guía para Claude Code

Este archivo se carga automáticamente por Claude Code cada vez que se abre una sesión
dentro de esta carpeta. Sirve como memoria persistente del proyecto entre PCs
(originalmente en Windows, migrado a Mac en agosto 2026).

## Qué es este proyecto

Dashboard interno en Streamlit que muestra gasto y leads de Meta Ads (Facebook/Instagram)
para Capitaria, desglosado por país (Chile, México, Uruguay, Perú) y campaña. Los datos
vienen de **Supermetrics** (que a su vez consulta la API de Meta Ads) y se cachean
diariamente en **Google Sheets** para no golpear la API en cada carga.

- **App en producción:** https://dashboard-meta-capitaria-cvzkk5urph6re4xq2rbm5k.streamlit.app/
- **Repo GitHub:** https://github.com/capitarialatam-bit/dashboard-meta-capitaria (branch `main`)
- **Deploy:** automático — Streamlit Community Cloud redespliega solo con cada push a `main`.

## Estructura

```
mcp-meta-capitaria/
├── dashboard/                  ← LA APP (esto es lo que corre en Streamlit Cloud)
│   ├── app.py                  ← entrypoint
│   ├── config.py                ← países, presupuestos, colores
│   ├── data/
│   │   ├── connector.py         ← orquesta caché (Google Sheets) + refresco (Supermetrics)
│   │   ├── supermetrics.py      ← cliente HTTP a la API MCP de Supermetrics (polling async)
│   │   └── aurora.py            ← lectura de Excel de leads (pestaña "Nuevos & Reingresos")
│   ├── components/               ← módulos de UI (charts, campañas, nuevos)
│   ├── credentials/              ← google_service_account.json (gitignored, NO subir)
│   ├── .env / .streamlit/secrets.toml  ← claves (gitignored, NO subir)
│   └── requirements.txt
├── mcp_meta.js, src/, package.json  ← servidor MCP separado (Claude Desktop), no relacionado al dashboard
└── debug_*.py                  ← scripts sueltos de debugging, no forman parte de la app
```

## Cómo correrlo en local (Mac)

```bash
cd dashboard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Necesita, en `dashboard/.env` **o** `dashboard/.streamlit/secrets.toml` (no están en git,
pedirle al usuario que los traiga de su gestor de secretos o de la config de Streamlit Cloud):

- `SUPERMETRICS_API_KEY`
- `GOOGLE_SHEET_ID`
- `gcp_service_account` (bloque TOML con las credenciales de la service account de Google, solo en `secrets.toml`)
- `dashboard/credentials/google_service_account.json` (mismo service account, en JSON)

En Streamlit Cloud estos mismos valores están cargados en **Settings → Secrets** del app —
si algo funciona en local pero no en producción (o viceversa), sospechar primero de un
secreto desincronizado entre `.env`/`secrets.toml` local y los Secrets de Streamlit Cloud.

## Incidente resuelto (2026-08-05) — para no repetir el diagnóstico

**Síntoma:** el dashboard se quedaba "cargando" indefinidamente y a veces se desconectaba.

**Causa raíz real:** la cuenta de Meta Ads conectada en Supermetrics (`act_336792180552844`)
había perdido permisos ("User may not have permissions to access account..."). Se resolvió
reconectando la cuenta en la integración de Supermetrics (fuera del código).

**Bug de código que agravaba el síntoma (ya arreglado, commit `d5bd4ab`):**
`_wait_result()` en `data/supermetrics.py` solo miraba `result["data"]["status"]`, que es
`null` cuando Supermetrics devuelve un error definitivo — así que el polling seguía
reintentando ciegamente ~150 segundos en vez de fallar rápido. Ahora revisa
`result["success"] is False` y lanza `SupermetricsError` de inmediato (~2-3s).

**Si vuelve a pasar "se queda cargando":** primero revisar si Supermetrics devuelve un
error de permisos/cuenta (se puede probar con un script suelto que llame
`data.supermetrics._run_query(...)` directo, sin pasar por Streamlit, para ver el JSON
crudo de respuesta). Recién si eso funciona bien, sospechar del código.

## Trabajo en progreso (sin terminar, sin pushear a propósito)

Puede haber cambios locales sueltos para una pestaña nueva "LinkedIn Ads"
(`app.py`, `config.py`, `components/linkedin.py`) — es una feature a medio construir,
no confundir con un bug. Antes de tocarla, confirmar con el usuario si se retoma o se
descarta.

## Reglas al trabajar en este repo

- El repo real y con git history vive en `C:\PROYECTOS\mcp-meta-capitaria` en la PC
  Windows original. En Mac, preferir un `git clone` limpio del repo de GitHub en vez de
  depender de una copia sincronizada por OneDrive/Drive (evita bloqueos de archivos de
  `.git` durante la sincronización).
- Nunca commitear `.env`, `.streamlit/secrets.toml` ni `credentials/*.json` (ya están en
  `.gitignore`, pero doble check antes de un `git add -A`).
- Antes de un `git push`, confirmar con el usuario — este repo hace deploy automático a
  producción en cuanto se pushea a `main`.

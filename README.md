# mcp-meta-capitaria

MCP Server para Meta Ads — Capitaria. Expone métricas de campañas a Claude Desktop.

## Requisitos

- Node.js 18+
- Cuenta Meta Business Manager con acceso a la cuenta publicitaria

## Setup

```bash
cd C:\PROYECTOS\mcp-meta-capitaria
npm install
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `META_TOKEN` | Access token de Meta (**caduca cada ~60 días**) |
| `META_ACCOUNT` | ID de cuenta publicitaria (`act_XXXXXXXXX`) |

## Registrar en Claude Desktop

Archivo: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "capitaria-meta": {
      "command": "node",
      "args": ["C:/PROYECTOS/mcp-meta-capitaria/src/index.js"],
      "env": {
        "META_TOKEN": "EAAxxxxx",
        "META_ACCOUNT": "act_xxxxxxx"
      }
    }
  }
}
```

Reiniciar Claude Desktop después de cualquier cambio en el config.

## Tools

| Tool | Parámetros | Descripción |
|---|---|---|
| `get_performance` | `year`, `month` | Gasto, leads y CPL por país |
| `get_campaigns` | `year`, `month` | Detalle por campaña con país y leads |

El período fiscal va del **día 26** del mes indicado al **día 25** del mes siguiente.

## Naming de campañas

El país se detecta automáticamente: posición `[0]` + posición `[4]` del nombre = código de país.

| Código | País |
|---|---|
| CL | Chile |
| MX | México |
| PE | Perú |
| UY | Uruguay |

## Renovar el token (cada ~60 días)

1. Ir a [Meta for Developers → Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Seleccionar la app → generar token con permisos `ads_read` y `ads_management`
3. Extender a token de larga duración (60 días)
4. Actualizar `META_TOKEN` en `claude_desktop_config.json`
5. Reiniciar Claude Desktop

**Alternativa permanente:** crear un System User Token en Meta Business Manager (no caduca).

## Error común

```
Error: Meta API error: Error validating access token
```
→ El token caducó. Renovar siguiendo los pasos de arriba.

# ─── 1. CREAR CARPETA Y ENTRAR ────────────────────────────────
mkdir mcp-meta-capitaria
cd mcp-meta-capitaria

# ─── 2. PACKAGE.JSON ──────────────────────────────────────────
# Crea el archivo package.json con este contenido:
# {
#   "name": "mcp-meta-capitaria",
#   "version": "1.0.0",
#   "type": "module",
#   "main": "index.js",
#   "dependencies": {
#     "@modelcontextprotocol/sdk": "^1.0.0",
#     "zod": "^3.22.0"
#   }
# }

npm install

# ─── 3. VARIABLES DE ENTORNO ──────────────────────────────────
# Crea un archivo .env (nunca lo subas a GitHub):
# META_TOKEN=EAAxxxxxxxxxxxxxxxxxx
# META_ACCOUNT=act_123456789

# ─── 4. AGREGAR AL claude_desktop_config.json ─────────────────
# Ruta en Windows: %APPDATA%\Claude\claude_desktop_config.json
#
# {
#   "mcpServers": {
#     "capitaria-meta": {
#       "command": "node",
#       "args": ["C:/ruta/completa/mcp-meta-capitaria/index.js"],
#       "env": {
#         "META_TOKEN": "EAAxxxxxxxxxxxxxxxxxx",
#         "META_ACCOUNT": "act_123456789"
#       }
#     }
#   }
# }

# ─── 5. REINICIAR CLAUDE DESKTOP ──────────────────────────────
# Cierra y vuelve a abrir Claude Desktop
# Verifica que aparezca el tool "capitaria-meta" en la lista de MCPs

# ─── 6. PROBAR EN CLAUDE CODE ─────────────────────────────────
# Escríbele a Claude:
# "Usa el tool get_performance para el mes fiscal 3 de 2026"

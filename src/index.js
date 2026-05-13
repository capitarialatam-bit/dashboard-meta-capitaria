import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// ── Configuración ─────────────────────────────────────────────────────────────
const META_TOKEN  = process.env.META_TOKEN;    // access token de Meta
const AD_ACCOUNT  = process.env.META_ACCOUNT;  // act_XXXXXXXXX
const API_VERSION = "v19.0";
const API_BASE    = `https://graph.facebook.com/${API_VERSION}`;

if (!META_TOKEN || !AD_ACCOUNT) {
  console.error("Error: se requieren las variables META_TOKEN y META_ACCOUNT.");
  process.exit(1);
}

// ── Parser de país desde nombre de campaña ────────────────────────────────────
// Convención de naming: posición 0 y 4 del nombre forman el código de país
// Ej: "CL_ES_..." → C(0) + L(4) → "CL"
const COUNTRY_MAP = { CL: "Chile", MX: "México", PE: "Perú", UY: "Uruguay" };

function getCountryCode(campaignName) {
  if (!campaignName || campaignName.length < 5) return "OTROS";
  const code = campaignName[0].toUpperCase() + campaignName[4].toUpperCase();
  return COUNTRY_MAP[code] ? code : "OTROS";
}

// ── Período fiscal: del 26 del mes al 25 del siguiente ───────────────────────
function getFiscalRange(year, month) {
  const since = `${year}-${String(month).padStart(2, "0")}-26`;
  const nextMonth = month === 12 ? 1 : month + 1;
  const nextYear  = month === 12 ? year + 1 : year;
  const until = `${nextYear}-${String(nextMonth).padStart(2, "0")}-25`;
  return { since, until };
}

// ── Llamada a Meta Insights API ───────────────────────────────────────────────
async function fetchMetaInsights(since, until) {
  const params = new URLSearchParams({
    access_token: META_TOKEN,
    level:        "campaign",
    fields:       "campaign_name,spend,actions,cost_per_action_type",
    time_range:   JSON.stringify({ since, until }),
    limit:        "500",
  });

  const res  = await fetch(`${API_BASE}/${AD_ACCOUNT}/insights?${params}`);
  const json = await res.json();

  if (json.error) throw new Error(`Meta API error: ${json.error.message}`);
  return json.data || [];
}

// ── Extrae leads de actions[] ─────────────────────────────────────────────────
function extractLeads(actions = []) {
  const action = actions.find(
    (a) => a.action_type === "lead" || a.action_type === "onsite_conversion.lead_grouped"
  );
  return action ? parseInt(action.value || 0) : 0;
}

// ── Agregación por país ───────────────────────────────────────────────────────
function aggregateByCountry(data) {
  const result = {};

  for (const row of data) {
    const code    = getCountryCode(row.campaign_name || "");
    const country = COUNTRY_MAP[code] || "Otros";

    if (!result[country]) {
      result[country] = { code, country, spend: 0, leads: 0, campaigns: 0 };
    }

    result[country].spend     += parseFloat(row.spend || 0);
    result[country].leads     += extractLeads(row.actions);
    result[country].campaigns += 1;
  }

  for (const r of Object.values(result)) {
    r.cpl   = r.leads > 0 ? +(r.spend / r.leads).toFixed(2) : 0;
    r.spend = +r.spend.toFixed(2);
  }

  return result;
}

// ── MCP Server ────────────────────────────────────────────────────────────────
const server = new McpServer({ name: "capitaria-meta-ads", version: "1.0.0" });

// TOOL: get_performance
server.tool(
  "get_performance",
  "Obtiene gasto, leads y CPL de Meta Ads agregado por país para el período fiscal indicado (26 del mes → 25 del siguiente).",
  {
    year:  z.number().describe("Año de inicio del período fiscal (ej: 2026)"),
    month: z.number().min(1).max(12).describe("Mes de inicio del período fiscal (ej: 3 → 26 mar al 25 abr)"),
  },
  async ({ year, month }) => {
    const { since, until } = getFiscalRange(year, month);
    const raw  = await fetchMetaInsights(since, until);
    const data = aggregateByCountry(raw);

    const summary = Object.values(data)
      .map((r) => `${r.country} (${r.code}): spend=$${r.spend} | leads=${r.leads} | CPL=$${r.cpl} | campañas=${r.campaigns}`)
      .join("\n");

    return {
      content: [{
        type: "text",
        text: `Período fiscal: ${since} → ${until}\n\n${summary}\n\nJSON:\n${JSON.stringify(data, null, 2)}`,
      }],
    };
  }
);

// TOOL: get_campaigns
server.tool(
  "get_campaigns",
  "Lista todas las campañas con su país detectado, gasto y leads para el período fiscal indicado.",
  {
    year:  z.number().describe("Año"),
    month: z.number().min(1).max(12).describe("Mes de inicio del período fiscal"),
  },
  async ({ year, month }) => {
    const { since, until } = getFiscalRange(year, month);
    const raw = await fetchMetaInsights(since, until);

    const rows = raw.map((row) => {
      const code    = getCountryCode(row.campaign_name || "");
      const country = COUNTRY_MAP[code] || "Otros";
      return {
        campaign: row.campaign_name,
        country,
        code,
        spend: +parseFloat(row.spend || 0).toFixed(2),
        leads: extractLeads(row.actions),
      };
    });

    const text = rows
      .map((r) => `[${r.code}] ${r.campaign} → $${r.spend} | ${r.leads} leads`)
      .join("\n");

    return {
      content: [{
        type: "text",
        text: `Campañas ${since} → ${until}:\n\n${text}\n\nJSON:\n${JSON.stringify(rows, null, 2)}`,
      }],
    };
  }
);

// ── Arrancar ──────────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP Capitaria Meta Ads → corriendo");

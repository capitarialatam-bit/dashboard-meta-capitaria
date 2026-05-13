// mcp-meta-capitaria/index.js
// MCP Server para Meta Ads API — Capitaria
// Ejecutar: node index.js

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// ─── CONFIGURACIÓN ────────────────────────────────────────────
const META_TOKEN   = process.env.META_TOKEN;   // tu access token
const AD_ACCOUNT   = process.env.META_ACCOUNT; // act_XXXXXXXXX
const API_VERSION  = "v19.0";
const API_BASE     = `https://graph.facebook.com/${API_VERSION}`;

// ─── PARSER DE PAÍS ───────────────────────────────────────────
const COUNTRY_MAP = { CL:"Chile", MX:"México", PE:"Perú", UY:"Uruguay" };

function getCountryCode(campaignName) {
  if (!campaignName || campaignName.length < 5) return "OTROS";
  const code = campaignName[0].toUpperCase() + campaignName[4].toUpperCase();
  return COUNTRY_MAP[code] ? code : "OTROS";
}

// ─── RANGO FISCAL (26 del mes → 25 del siguiente) ─────────────
function getFiscalRange(year, month) {
  // month: 1-12
  const since = `${year}-${String(month).padStart(2,"0")}-26`;
  const nextMonth = month === 12 ? 1 : month + 1;
  const nextYear  = month === 12 ? year + 1 : year;
  const until = `${nextYear}-${String(nextMonth).padStart(2,"0")}-25`;
  return { since, until };
}

// ─── LLAMADA A META API ───────────────────────────────────────
async function fetchMetaInsights(since, until) {
  const fields = [
    "campaign_name",
    "spend",
    "actions",
    "cost_per_action_type"
  ].join(",");

  const params = new URLSearchParams({
    access_token: META_TOKEN,
    level:        "campaign",
    fields,
    time_range:   JSON.stringify({ since, until }),
    limit:        "500"
  });

  const url = `${API_BASE}/${AD_ACCOUNT}/insights?${params}`;
  const res  = await fetch(url);
  const json = await res.json();

  if (json.error) throw new Error(`Meta API error: ${json.error.message}`);
  return json.data || [];
}

// ─── AGREGACIÓN POR PAÍS ──────────────────────────────────────
function aggregateByCountry(data) {
  const result = {};

  for (const row of data) {
    const code    = getCountryCode(row.campaign_name || "");
    const country = COUNTRY_MAP[code] || "Otros";

    if (!result[country]) {
      result[country] = { code, country, spend: 0, leads: 0, campaigns: 0 };
    }

    result[country].spend     += parseFloat(row.spend || 0);
    result[country].campaigns += 1;

    // Extraer leads de actions[]
    const actions = row.actions || [];
    const leadAction = actions.find(a =>
      a.action_type === "lead" ||
      a.action_type === "onsite_conversion.lead_grouped"
    );
    if (leadAction) {
      result[country].leads += parseInt(leadAction.value || 0);
    }
  }

  // Calcular CPL por país
  for (const key of Object.keys(result)) {
    const r = result[key];
    r.cpl   = r.leads > 0 ? +(r.spend / r.leads).toFixed(2) : 0;
    r.spend = +r.spend.toFixed(2);
  }

  return result;
}

// ─── MCP SERVER ───────────────────────────────────────────────
const server = new McpServer({
  name:    "capitaria-meta-ads",
  version: "1.0.0"
});

// TOOL: get_performance
server.tool(
  "get_performance",
  "Obtiene gasto, leads y CPL de Meta Ads por país para el mes fiscal indicado",
  {
    year:  z.number().describe("Año del inicio del mes fiscal (ej: 2026)"),
    month: z.number().min(1).max(12).describe("Mes de inicio del período fiscal (ej: 3 para 26 mar – 25 abr)")
  },
  async ({ year, month }) => {
    const { since, until } = getFiscalRange(year, month);
    const raw  = await fetchMetaInsights(since, until);
    const data = aggregateByCountry(raw);

    const summary = Object.values(data).map(r =>
      `${r.country} (${r.code}): spend=$${r.spend} | leads=${r.leads} | CPL=$${r.cpl} | campañas=${r.campaigns}`
    ).join("\n");

    return {
      content: [{
        type: "text",
        text: `Período fiscal: ${since} → ${until}\n\n${summary}\n\nJSON:\n${JSON.stringify(data, null, 2)}`
      }]
    };
  }
);

// TOOL: get_campaigns
server.tool(
  "get_campaigns",
  "Lista todas las campañas activas con su país, gasto y leads",
  {
    year:  z.number().describe("Año"),
    month: z.number().min(1).max(12).describe("Mes de inicio del período fiscal")
  },
  async ({ year, month }) => {
    const { since, until } = getFiscalRange(year, month);
    const raw = await fetchMetaInsights(since, until);

    const rows = raw.map(row => {
      const code    = getCountryCode(row.campaign_name || "");
      const country = COUNTRY_MAP[code] || "Otros";
      const leads   = (row.actions || []).find(a =>
        a.action_type === "lead" ||
        a.action_type === "onsite_conversion.lead_grouped"
      );
      return {
        campaign: row.campaign_name,
        country,
        code,
        spend:  +parseFloat(row.spend || 0).toFixed(2),
        leads:  leads ? parseInt(leads.value) : 0
      };
    });

    const text = rows.map(r =>
      `[${r.code}] ${r.campaign} → $${r.spend} | ${r.leads} leads`
    ).join("\n");

    return {
      content: [{
        type: "text",
        text: `Campañas ${since} → ${until}:\n\n${text}\n\nJSON:\n${JSON.stringify(rows, null, 2)}`
      }]
    };
  }
);

// ─── ARRANCAR ─────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP Capitaria Meta Ads — corriendo");

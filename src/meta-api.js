const GRAPH_API_VERSION = 'v21.0';
const BASE_URL = `https://graph.facebook.com/${GRAPH_API_VERSION}`;

export class MetaApiClient {
  constructor(accessToken) {
    this.accessToken = accessToken;
  }

  async request(path, { method = 'GET', params = {}, body = null } = {}) {
    const url = new URL(`${BASE_URL}${path}`);
    url.searchParams.set('access_token', this.accessToken);

    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }

    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) options.body = JSON.stringify(body);

    const res = await fetch(url.toString(), options);
    const data = await res.json();

    if (data.error) {
      throw new Error(`Meta API error ${data.error.code}: ${data.error.message}`);
    }

    return data;
  }

  // ── Cuentas ──────────────────────────────────────────────────────────────

  getAdAccounts(fields = 'id,name,account_status,currency,timezone_name,amount_spent') {
    return this.request('/me/adaccounts', { params: { fields } });
  }

  getAdAccount(accountId, fields = 'id,name,account_status,currency,timezone_name,amount_spent,balance') {
    return this.request(`/act_${accountId}`, { params: { fields } });
  }

  // ── Campañas ─────────────────────────────────────────────────────────────

  getCampaigns(accountId, fields = 'id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time') {
    return this.request(`/act_${accountId}/campaigns`, { params: { fields } });
  }

  getCampaign(campaignId, fields = 'id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time,insights') {
    return this.request(`/${campaignId}`, { params: { fields } });
  }

  createCampaign(accountId, { name, objective, status = 'PAUSED', daily_budget, lifetime_budget, start_time, stop_time, special_ad_categories = [] }) {
    return this.request(`/act_${accountId}/campaigns`, {
      method: 'POST',
      body: { name, objective, status, daily_budget, lifetime_budget, start_time, stop_time, special_ad_categories },
    });
  }

  updateCampaign(campaignId, fields) {
    return this.request(`/${campaignId}`, { method: 'POST', body: fields });
  }

  deleteCampaign(campaignId) {
    return this.request(`/${campaignId}`, { method: 'DELETE' });
  }

  // ── Conjuntos de anuncios ─────────────────────────────────────────────────

  getAdSets(accountId, fields = 'id,name,status,campaign_id,daily_budget,lifetime_budget,start_time,end_time,targeting,bid_amount') {
    return this.request(`/act_${accountId}/adsets`, { params: { fields } });
  }

  getAdSet(adSetId, fields = 'id,name,status,campaign_id,daily_budget,lifetime_budget,targeting,optimization_goal,billing_event') {
    return this.request(`/${adSetId}`, { params: { fields } });
  }

  createAdSet(accountId, data) {
    return this.request(`/act_${accountId}/adsets`, { method: 'POST', body: data });
  }

  updateAdSet(adSetId, fields) {
    return this.request(`/${adSetId}`, { method: 'POST', body: fields });
  }

  // ── Anuncios ──────────────────────────────────────────────────────────────

  getAds(accountId, fields = 'id,name,status,adset_id,campaign_id,creative,created_time') {
    return this.request(`/act_${accountId}/ads`, { params: { fields } });
  }

  getAd(adId, fields = 'id,name,status,adset_id,campaign_id,creative,created_time') {
    return this.request(`/${adId}`, { params: { fields } });
  }

  // ── Métricas (Insights) ───────────────────────────────────────────────────

  getInsights(objectId, { datePreset, since, until, fields, level = 'ad', breakdowns } = {}) {
    const params = { level, fields: fields ?? 'impressions,clicks,spend,ctr,cpc,cpm,reach,frequency,actions' };
    if (datePreset) params.date_preset = datePreset;
    if (since && until) params.time_range = JSON.stringify({ since, until });
    if (breakdowns) params.breakdowns = breakdowns;
    return this.request(`/${objectId}/insights`, { params });
  }
}

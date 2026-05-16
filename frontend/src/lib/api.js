const API_BASE = import.meta.env.VITE_API_BASE || "";

// Helper to get auth token from localStorage
function getAuthToken() {
  return localStorage.getItem("auth_token");
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? 90000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    // Add Authorization header if token exists
    const token = getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      headers,
      signal: controller.signal,
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let detailText = "";
      try {
        const parsed = JSON.parse(errorText);
        const detail = parsed?.detail;
        detailText = detail ? (typeof detail === "string" ? detail : JSON.stringify(detail)) : "";
      } catch {
        // Keep raw text fallback below.
      }
      throw new Error(detailText || errorText || `Request failed with ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Request timed out. Try again or use a smaller target scope.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = {
  request,
  health: () => request("/api/health"),
  history: (limit = 10) => request(`/api/history?limit=${limit}`),
  dashboard: () => request("/api/dashboard"),
  liveStart: (target) => request("/api/scan/live/start", { method: "POST", body: JSON.stringify({ target }) }),
  liveStatus: (jobId) => request(`/api/scan/live/${jobId}`),
  liveCancel: (jobId) => request(`/api/scan/live/${jobId}/cancel`, { method: "POST" }),
  recon: (target) => request("/api/scan/recon", { method: "POST", body: JSON.stringify({ target }) }),
  vulnerability: (target) =>
    request("/api/scan/vulnerability", { method: "POST", body: JSON.stringify({ target }) }),
  defence: (target) => request("/api/scan/defence", { method: "POST", body: JSON.stringify({ target }) }),
  siem: (target) => request("/api/scan/siem", { method: "POST", body: JSON.stringify({ target }) }),
  virustotal: (target) => request("/api/scan/virustotal", { method: "POST", body: JSON.stringify({ target }) }),
  shodan: (target) => request("/api/scan/shodan", { method: "POST", body: JSON.stringify({ target }) }),
  abuseipdb: (target) => request("/api/scan/abuseipdb", { method: "POST", body: JSON.stringify({ target }) }),
  autoScan: (target) => request("/api/scan/auto", { method: "POST", body: JSON.stringify({ target }), timeoutMs: 300000 }),
  customScan: (target, modules) =>
    request("/api/scan/custom", {
      method: "POST",
      body: JSON.stringify({ target, modules }),
      timeoutMs: 300000,
    }),
  scanStatus: (jobId) => request(`/api/scan/status/${jobId}`),
  policy: (policyId, orgName) =>
    request("/api/policy/generate", {
      method: "POST",
      body: JSON.stringify({ policy_id: policyId, org_name: orgName }),
    }),
  report: (payload) => request("/api/report/generate", { method: "POST", body: JSON.stringify(payload) }),
  scanHistory: (limit = 20) => request(`/api/scan/history?limit=${limit}`),
  getApiKeysStatus: () => request("/api/admin/api-keys"),
  updateApiKey: (key_name, key_value) => request("/api/admin/api-keys", { 
    method: "PUT", 
    body: JSON.stringify({ key_name, key_value }) 
  }),
  getSchedules: () => request("/api/schedules"),
  createSchedule: (data) => request("/api/schedules", { method: "POST", body: JSON.stringify(data) }),
  deleteSchedule: (id) => request(`/api/schedules/${id}`, { method: "DELETE" }),
  toggleSchedule: (id) => request(`/api/schedules/${id}/toggle`, { method: "PUT" }),
  scoreHistory: (target, limit = 30) => request(`/api/scores/history?target=${encodeURIComponent(target)}&limit=${limit}`),
  saveScore: (data) => request("/api/scores/save", { method: "POST", body: JSON.stringify(data) }),
  listTeams: () => request("/api/teams"),
  createTeam: (data) => request("/api/teams", { method: "POST", body: JSON.stringify(data) }),
  getTeamMembers: (teamId) => request(`/api/teams/${teamId}/members`),
  getTeamScans: (teamId) => request(`/api/teams/${teamId}/scans`),
  inviteTeamMember: (teamId, data) => request(`/api/teams/${teamId}/invite`, { method: "POST", body: JSON.stringify(data) }),
  removeTeamMember: (teamId, userId) => request(`/api/teams/${teamId}/members/${userId}`, { method: "DELETE" }),
  shareTeamScan: (teamId, scanId) => request(`/api/teams/${teamId}/share-scan/${scanId}`, { method: "POST" }),
  listWebhooks: () => request("/api/webhooks"),
  createWebhook: (data) => request("/api/webhooks", { method: "POST", body: JSON.stringify(data) }),
  deleteWebhook: (id) => request(`/api/webhooks/${id}`, { method: "DELETE" }),
  updateWebhook: (id, data) => request(`/api/webhooks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  testWebhook: (webhookId = null, webhookUrl = null) => {
    const params = new URLSearchParams();
    if (webhookId) params.append("webhook_id", webhookId);
    if (webhookUrl) params.append("webhook_url", webhookUrl);
    return request(`/api/webhooks/test?${params.toString()}`, { method: "POST" });
  },
};

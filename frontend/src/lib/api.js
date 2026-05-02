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
  autoScan: (target) => request("/api/scan/auto", { method: "POST", body: JSON.stringify({ target }), timeoutMs: 300000 }),
  customScan: (target, modules) =>
    request("/api/scan/custom", {
      method: "POST",
      body: JSON.stringify({ target, modules }),
      timeoutMs: 300000,
    }),
  policy: (policyId, orgName) =>
    request("/api/policy/generate", {
      method: "POST",
      body: JSON.stringify({ policy_id: policyId, org_name: orgName }),
    }),
  report: (payload) => request("/api/report/generate", { method: "POST", body: JSON.stringify(payload) }),
  scanHistory: (limit = 20) => request(`/api/scan/history?limit=${limit}`),
};

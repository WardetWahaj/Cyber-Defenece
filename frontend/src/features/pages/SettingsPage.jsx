import { useEffect, useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";

export default function SettingsPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [message, setMessage] = useState("");
  const [webhooks, setWebhooks] = useState([]);
  const [loadingWebhooks, setLoadingWebhooks] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [notifyComplete, setNotifyComplete] = useState(true);
  const [notifyCritical, setNotifyCritical] = useState(true);
  const [addingWebhook, setAddingWebhook] = useState(false);
  const [testingWebhook, setTestingWebhook] = useState(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "offline" }));
    loadWebhooks();
  }, [user]);

  async function loadWebhooks() {
    try {
      setLoadingWebhooks(true);
      const data = await api.listWebhooks();
      setWebhooks(data || []);
    } catch (err) {
      console.error("Failed to load webhooks:", err);
    } finally {
      setLoadingWebhooks(false);
    }
  }

  async function addWebhook() {
    if (!webhookUrl.trim()) {
      setMessage("❌ Webhook URL is required");
      return;
    }

    try {
      setAddingWebhook(true);
      setMessage("");
      await api.createWebhook({
        webhook_url: webhookUrl,
        webhook_type: "slack",
        notify_on_complete: notifyComplete,
        notify_on_critical: notifyCritical,
      });
      setWebhookUrl("");
      setMessage("✓ Webhook added successfully");
      await loadWebhooks();
    } catch (err) {
      setMessage(`❌ ${err.message}`);
    } finally {
      setAddingWebhook(false);
    }
  }

  async function deleteWebhook(id) {
    if (!confirm("Delete this webhook configuration?")) return;

    try {
      setMessage("");
      await api.deleteWebhook(id);
      setMessage("✓ Webhook deleted");
      await loadWebhooks();
    } catch (err) {
      setMessage(`❌ ${err.message}`);
    }
  }

  async function testWebhook(id) {
    try {
      setMessage("");
      setTestingWebhook(id);
      await api.testWebhook(id);
      setMessage("✓ Test notification sent! Check Slack.");
    } catch (err) {
      setMessage(`❌ ${err.message}`);
    } finally {
      setTestingWebhook(null);
    }
  }

  async function refreshHealth() {
    try {
      const h = await api.health();
      setHealth(h);
    } catch {
      setHealth({ status: "offline" });
    }
  }

  const isAdmin = user?.role === "admin";

  return (
    <>
      <PageTitle title="Settings & API Integrations" subtitle="Connection status and environment diagnostics." />
      {message && <p style={{ color: message.startsWith("✓") ? "#45dfa4" : "#ffb4ab", fontSize: 12 }}>{message}</p>}
      {health?.status === "offline" && <p style={{ color: "#ffb4ab", fontSize: 12 }}>Backend health check is offline.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start", minHeight: "100vh" }}>
        <section style={{ display: "grid", gap: 24 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <Card title="INTEGRATION HEALTH">
              <div style={{ display: "grid", gap: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Status</span>
                  <Badge variant={health?.status === "online" ? "success" : "warning"}>
                    {health?.status ? health.status.toUpperCase() : "UNKNOWN"}
                  </Badge>
                </div>
                {health?.version && (
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>Backend Version</span>
                    <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{health.version}</span>
                  </div>
                )}
                {health?.nuclei_available !== undefined && (
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>Nuclei Scanner</span>
                    <Badge variant={health.nuclei_available ? "success" : "warning"}>
                      {health.nuclei_available ? "AVAILABLE" : "UNAVAILABLE"}
                    </Badge>
                  </div>
                )}
              </div>
            </Card>

            <Card title="AUTH HISTORY">
              <div style={{ display: "grid", gap: 12, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                <p>Auth event logging coming soon.</p>
              </div>
            </Card>
          </div>

          <Card title="📬 NOTIFICATIONS">
            <div style={{ display: "grid", gap: 16 }}>
              <div style={{ display: "grid", gap: 12 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--text-muted)" }}>
                    Slack Webhook URL
                  </label>
                  <input
                    type="url"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    placeholder="https://hooks.slack.com/services/..."
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 6,
                      border: "1px solid var(--surface-high)",
                      background: "var(--surface-low)",
                      color: "var(--text)",
                      fontSize: 12,
                      boxSizing: "border-box",
                      fontFamily: "monospace",
                    }}
                  />
                  <p style={{ fontSize: 10, color: "var(--text-muted)", margin: "6px 0 0 0" }}>
                    Get webhook URL from your Slack workspace settings
                  </p>
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 12 }}>
                    <input
                      type="checkbox"
                      checked={notifyComplete}
                      onChange={(e) => setNotifyComplete(e.target.checked)}
                      style={{ cursor: "pointer" }}
                    />
                    Notify when scans complete
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 12 }}>
                    <input
                      type="checkbox"
                      checked={notifyCritical}
                      onChange={(e) => setNotifyCritical(e.target.checked)}
                      style={{ cursor: "pointer" }}
                    />
                    Alert on critical vulnerabilities
                  </label>
                </div>

                <button
                  onClick={addWebhook}
                  disabled={addingWebhook || !webhookUrl.trim()}
                  style={{
                    padding: "10px 16px",
                    borderRadius: 6,
                    border: "none",
                    background: "var(--primary)",
                    color: "white",
                    cursor: "pointer",
                    fontSize: 12,
                    fontWeight: 600,
                    opacity: addingWebhook || !webhookUrl.trim() ? 0.6 : 1,
                  }}
                >
                  {addingWebhook ? "Adding..." : "Add Webhook"}
                </button>
              </div>

              {webhooks.length > 0 && (
                <div style={{ display: "grid", gap: 10, borderTop: "1px solid var(--surface-high)", paddingTop: 12 }}>
                  <p style={{ margin: 0, fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>
                    CONFIGURED WEBHOOKS ({webhooks.length})
                  </p>
                  {webhooks.map((wh) => (
                    <div
                      key={wh.id}
                      style={{
                        background: "var(--surface-high)",
                        border: "1px solid rgba(59, 130, 246, 0.2)",
                        borderRadius: 6,
                        padding: 10,
                        display: "grid",
                        gap: 8,
                      }}
                    >
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <code style={{ fontSize: 10, color: "var(--text-muted)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {wh.webhook_url}
                        </code>
                        <Badge variant="secondary" style={{ whiteSpace: "nowrap" }}>
                          {wh.is_active ? "ACTIVE" : "INACTIVE"}
                        </Badge>
                      </div>
                      <div style={{ display: "flex", gap: 6, fontSize: 10, color: "var(--text-muted)" }}>
                        {wh.notify_on_complete && <span>✓ Complete</span>}
                        {wh.notify_on_critical && <span>✓ Critical</span>}
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>
                        <button
                          onClick={() => testWebhook(wh.id)}
                          disabled={testingWebhook === wh.id}
                          style={{
                            padding: "6px 12px",
                            borderRadius: 4,
                            border: "1px solid var(--primary)",
                            background: "transparent",
                            color: "var(--primary)",
                            cursor: "pointer",
                            fontSize: 11,
                            fontWeight: 600,
                          }}
                        >
                          {testingWebhook === wh.id ? "Testing..." : "Test"}
                        </button>
                        <button
                          onClick={() => deleteWebhook(wh.id)}
                          style={{
                            padding: "6px 12px",
                            borderRadius: 4,
                            border: "1px solid #ff6b6b",
                            background: "transparent",
                            color: "#ff6b6b",
                            cursor: "pointer",
                            fontSize: 11,
                            fontWeight: 600,
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </section>

        <Card title="PROFILE" style={{ height: "fit-content", position: "sticky", top: 80 }}>
          <div style={{ display: "grid", placeItems: "center", textAlign: "center", gap: 12 }}>
            <div style={{ width: 90, height: 90, borderRadius: 18, border: "2px solid var(--primary)", padding: 4, background: "var(--surface-high)", display: "grid", placeItems: "center", fontSize: 36, fontWeight: 800, color: "var(--primary)", flexShrink: 0 }}>
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, wordBreak: "break-word" }}>{user?.full_name || "User"}</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", wordBreak: "break-word" }}>{user?.email}</div>
            <div style={{ fontSize: 11, color: "#3B82F6", fontWeight: 800, letterSpacing: "0.16em" }}>
              {user?.organization || "ORGANIZATION"}
            </div>
            <div style={{ width: "100%", background: "var(--surface-highest)", border: "1px solid var(--ghost)", padding: 12, borderRadius: 6, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Account Status</span>
              <Badge variant="success">ACTIVE</Badge>
            </div>
            {isAdmin && (
              <div style={{ width: "100%", background: "var(--surface-highest)", border: "1px solid var(--primary)", padding: 12, borderRadius: 6, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Admin Privileges</span>
                <Badge variant="primary">ADMIN</Badge>
              </div>
            )}
          </div>
        </Card>
      </div>
    </>
  );
}



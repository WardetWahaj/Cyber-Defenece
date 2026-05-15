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
  const [shodanKey, setShodanKey] = useState("");
  const [abuseipdbKey, setAbuseipdbKey] = useState("");
  const [virustotalKey, setVirustotalKey] = useState("");
  const [wpscanKey, setWpscanKey] = useState("");
  const [nvdKey, setNvdKey] = useState("");
  const [keysStatus, setKeysStatus] = useState({});
  const [savingKey, setSavingKey] = useState("");
  const [services, setServices] = useState([
    ["Nuclei", "connected"],
    ["WPScan", "connected"],
    ["VirusTotal", "attention"],
    ["Sucuri", "connected"],
    ["SecurityHeaders", "connected"],
    ["Cloudflare", "connected"],
  ]);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "offline" }));
    // Load API keys configuration status
    if (user?.role === "admin") {
      api.getApiKeysStatus()
        .then(data => setKeysStatus(data.keys || {}))
        .catch(() => {});
    }
  }, [user]);

  async function refreshHealth() {
    try {
      const h = await api.health();
      setHealth(h);
    } catch {
      setHealth({ status: "offline" });
    }
  }

  async function saveApiKey(keyName, keyValue, setter) {
    if (!keyValue.trim()) return;
    setSavingKey(keyName);
    try {
      await api.updateApiKey(keyName, keyValue);
      setKeysStatus(prev => ({ ...prev, [keyName]: true }));
      setter("");
      setMessage(`✓ ${keyName} updated successfully!`);
      setTimeout(() => setMessage(""), 3000);
    } catch (e) {
      setMessage(`✗ Failed to update ${keyName}: ${e.message}`);
      setTimeout(() => setMessage(""), 4000);
    } finally {
      setSavingKey("");
    }
  }

  async function onProviderAction(name, state) {
    const defaultValue = state === "attention" ? "paste-new-key" : "current-key";
    const value = window.prompt(`${state === "attention" ? "Renew" : "Edit"} key for ${name}:`, defaultValue);
    if (!value) return;

    setMessage(`${name} key ${state === "attention" ? "renewed" : "updated"} successfully.`);
    setServices((prev) => prev.map(([n, s]) => (n === name ? [n, "connected"] : [n, s])));
    await refreshHealth();
  }

  function addProvider() {
    const name = window.prompt("Provider name:", "NewProvider");
    if (!name) return;
    setServices((prev) => [...prev, [name, "attention"]]);
    setMessage(`${name} provider added. Configure key to connect.`);
  }

  const isAdmin = user?.role === "admin";

  return (
    <>
      <PageTitle title="Settings & API Integrations" subtitle="Connection status and environment diagnostics." />
      {message && <p style={{ color: message.startsWith("✓") ? "#45dfa4" : "#ffb4ab", fontSize: 12 }}>{message}</p>}
      {health?.status === "offline" && <p style={{ color: "#ffb4ab", fontSize: 12 }}>Backend health check is offline.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start", minHeight: "100vh" }}>
        <section style={{ display: "grid", gap: 24 }}>
          {isAdmin && (
            <Card title="🔑 API KEY MANAGEMENT" subtitle="Configure API keys for threat intelligence modules">
              <div style={{ display: "grid", gap: 16 }}>
                {/* Shodan */}
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: keysStatus.SHODAN_API_KEY ? "var(--success)" : "var(--critical)", display: "inline-block" }} />
                    Shodan API Key
                    <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 400 }}>
                      {keysStatus.SHODAN_API_KEY ? "(Configured)" : "(Not configured)"}
                    </span>
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder="Enter Shodan API Key..."
                      value={shodanKey}
                      onChange={(e) => setShodanKey(e.target.value)}
                      style={{ flex: 1, padding: "8px 12px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6, fontSize: 13 }}
                    />
                    <button
                      onClick={() => saveApiKey("SHODAN_API_KEY", shodanKey, setShodanKey)}
                      disabled={savingKey === "SHODAN_API_KEY" || !shodanKey.trim()}
                      style={{ padding: "8px 16px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", opacity: savingKey === "SHODAN_API_KEY" || !shodanKey.trim() ? 0.5 : 1, fontWeight: 600 }}
                    >
                      {savingKey === "SHODAN_API_KEY" ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>

                {/* AbuseIPDB */}
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: keysStatus.ABUSEIPDB_API_KEY ? "var(--success)" : "var(--critical)", display: "inline-block" }} />
                    AbuseIPDB API Key
                    <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 400 }}>
                      {keysStatus.ABUSEIPDB_API_KEY ? "(Configured)" : "(Not configured)"}
                    </span>
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder="Enter AbuseIPDB API Key..."
                      value={abuseipdbKey}
                      onChange={(e) => setAbuseipdbKey(e.target.value)}
                      style={{ flex: 1, padding: "8px 12px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6, fontSize: 13 }}
                    />
                    <button
                      onClick={() => saveApiKey("ABUSEIPDB_API_KEY", abuseipdbKey, setAbuseipdbKey)}
                      disabled={savingKey === "ABUSEIPDB_API_KEY" || !abuseipdbKey.trim()}
                      style={{ padding: "8px 16px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", opacity: savingKey === "ABUSEIPDB_API_KEY" || !abuseipdbKey.trim() ? 0.5 : 1, fontWeight: 600 }}
                    >
                      {savingKey === "ABUSEIPDB_API_KEY" ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>

                {/* VirusTotal */}
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: keysStatus.VIRUSTOTAL_API_KEY ? "var(--success)" : "var(--critical)", display: "inline-block" }} />
                    VirusTotal API Key
                    <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 400 }}>
                      {keysStatus.VIRUSTOTAL_API_KEY ? "(Configured)" : "(Not configured)"}
                    </span>
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder="Enter VirusTotal API Key..."
                      value={virustotalKey}
                      onChange={(e) => setVirustotalKey(e.target.value)}
                      style={{ flex: 1, padding: "8px 12px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6, fontSize: 13 }}
                    />
                    <button
                      onClick={() => saveApiKey("VIRUSTOTAL_API_KEY", virustotalKey, setVirustotalKey)}
                      disabled={savingKey === "VIRUSTOTAL_API_KEY" || !virustotalKey.trim()}
                      style={{ padding: "8px 16px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", opacity: savingKey === "VIRUSTOTAL_API_KEY" || !virustotalKey.trim() ? 0.5 : 1, fontWeight: 600 }}
                    >
                      {savingKey === "VIRUSTOTAL_API_KEY" ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>

                {/* WPScan */}
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: keysStatus.WPSCAN_API_KEY ? "var(--success)" : "var(--critical)", display: "inline-block" }} />
                    WPScan API Key
                    <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 400 }}>
                      {keysStatus.WPSCAN_API_KEY ? "(Configured)" : "(Not configured)"}
                    </span>
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder="Enter WPScan API Key..."
                      value={wpscanKey}
                      onChange={(e) => setWpscanKey(e.target.value)}
                      style={{ flex: 1, padding: "8px 12px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6, fontSize: 13 }}
                    />
                    <button
                      onClick={() => saveApiKey("WPSCAN_API_KEY", wpscanKey, setWpscanKey)}
                      disabled={savingKey === "WPSCAN_API_KEY" || !wpscanKey.trim()}
                      style={{ padding: "8px 16px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", opacity: savingKey === "WPSCAN_API_KEY" || !wpscanKey.trim() ? 0.5 : 1, fontWeight: 600 }}
                    >
                      {savingKey === "WPSCAN_API_KEY" ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>

                {/* NVD */}
                <div>
                  <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: keysStatus.NVD_API_KEY ? "var(--success)" : "var(--critical)", display: "inline-block" }} />
                    NVD API Key
                    <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 400 }}>
                      {keysStatus.NVD_API_KEY ? "(Configured)" : "(Not configured)"}
                    </span>
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder="Enter NVD API Key..."
                      value={nvdKey}
                      onChange={(e) => setNvdKey(e.target.value)}
                      style={{ flex: 1, padding: "8px 12px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6, fontSize: 13 }}
                    />
                    <button
                      onClick={() => saveApiKey("NVD_API_KEY", nvdKey, setNvdKey)}
                      disabled={savingKey === "NVD_API_KEY" || !nvdKey.trim()}
                      style={{ padding: "8px 16px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", opacity: savingKey === "NVD_API_KEY" || !nvdKey.trim() ? 0.5 : 1, fontWeight: 600 }}
                    >
                      {savingKey === "NVD_API_KEY" ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>

                <div style={{ fontSize: 12, color: "var(--text-muted)", paddingTop: 8, borderTop: "1px solid var(--ghost)" }}>
                  <p style={{ margin: "8px 0" }}>💡 Keys are saved to Heroku Config Vars and take effect immediately.</p>
                  <p style={{ margin: "4px 0" }}>🔒 Keys are never displayed in plaintext - only the configuration status is shown.</p>
                </div>
              </div>
            </Card>
          )}

          <Card title="API INTEGRATIONS" right={<Buttonish onClick={addProvider} />}>
            <div style={{ display: "grid", gap: 12 }}>
              {services.map(([name, state]) => (
                <div key={name} style={{ background: "var(--surface)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: "var(--text)" }}>{name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{name === "VirusTotal" ? "Aggregated antivirus results and reputation checks." : `Integration for ${name.toLowerCase()} telemetry.`}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                    <Badge variant={state === "connected" ? "success" : "warning"}>{state.toUpperCase()}</Badge>
                    <button className="btn btn-secondary" style={{ padding: "8px 12px", whiteSpace: "nowrap" }} onClick={() => onProviderAction(name, state)}>{state === "attention" ? "RENEW KEY" : "EDIT KEY"}</button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <Card title="INTEGRATION HEALTH">
              <div style={{ display: "grid", placeItems: "center", padding: "8px 0 12px" }}>
                <div style={{ width: 160, height: 160, borderRadius: "50%", background: "conic-gradient(var(--primary) 0 83%, var(--surface-high) 83% 100%)", display: "grid", placeItems: "center" }}>
                  <div style={{ width: 120, height: 120, borderRadius: "50%", background: "var(--surface)", display: "grid", placeItems: "center", textAlign: "center" }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: "var(--text)" }}>83%</div>
                    <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.15em" }}>Operational</div>
                  </div>
                </div>
              </div>
              <div style={{ display: "grid", gap: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Active Nodes</span><span>5/6</span></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Latency (Avg)</span><span>142ms</span></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Fail Rate</span><span>2.1%</span></div>
              </div>
            </Card>

            <Card title="AUTH HISTORY">
              <div style={{ display: "grid", gap: 12 }}>
                <div style={{ borderLeft: "3px solid #45dfa4", paddingLeft: 8 }}>
                  <div style={{ fontSize: 13 }}>Cloudflare token refreshed</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Today, 09:12 AM</div>
                </div>
                <div style={{ borderLeft: "3px solid #ffb4ab", paddingLeft: 8 }}>
                  <div style={{ fontSize: 13 }}>VirusTotal key expired</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Yesterday, 11:45 PM</div>
                </div>
                <div style={{ borderLeft: "3px solid #45dfa4", paddingLeft: 8 }}>
                  <div style={{ fontSize: 13 }}>Sucuri connection stable</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Aug 24, 02:20 PM</div>
                </div>
              </div>
            </Card>
          </div>
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

function Buttonish({ onClick }) {
  return (
    <button className="btn btn-primary" style={{ padding: "8px 12px" }} onClick={onClick}>
      + ADD PROVIDER
    </button>
  );
}

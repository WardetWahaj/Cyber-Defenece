import { useEffect, useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";

export default function AdminPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [keyMessage, setKeyMessage] = useState("");
  const [shodanKey, setShodanKey] = useState("");
  const [abuseipdbKey, setAbuseipdbKey] = useState("");
  const [virusTotalKey, setVirusTotalKey] = useState("");
  const [wpscanKey, setWpscanKey] = useState("");
  const [nvdKey, setNvdKey] = useState("");
  const [updatingKeys, setUpdatingKeys] = useState(false);

  // Check if user is admin
  if (user?.role !== "admin") {
    return (
      <>
        <PageTitle title="Admin Panel" subtitle="Administration controls" />
        <Card title="ACCESS DENIED">
          <p style={{ color: "#ffb4ab" }}>You do not have permission to access this page. Only administrators can view this section.</p>
        </Card>
      </>
    );
  }

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      setLoading(true);
      const [usersData, scansData] = await Promise.all([
        api.request("/api/admin/users"),
        api.request("/api/admin/scans", { method: "GET" }),
      ]);
      setUsers(usersData.users || []);
      setScans(scansData.scans || []);
    } catch (e) {
      setMessage(`Error loading admin data: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function updateUserRole(userId, newRole) {
    try {
      const result = await api.request(`/api/admin/users/${userId}/role`, {
        method: "PUT",
        body: JSON.stringify({ role: newRole }),
      });
      setMessage(`User role updated to ${newRole}`);
      fetchData();
    } catch (e) {
      setMessage(`Error updating user role: ${e.message}`);
    }
  }

  async function saveApiKeys() {
    try {
      setUpdatingKeys(true);
      const payload = {};
      if (shodanKey) payload.shodan_api_key = shodanKey;
      if (abuseipdbKey) payload.abuseipdb_api_key = abuseipdbKey;
      if (virusTotalKey) payload.virustotal_api_key = virusTotalKey;
      if (wpscanKey) payload.wpscan_api_key = wpscanKey;
      if (nvdKey) payload.nvd_api_key = nvdKey;

      const result = await api.request("/api/admin/config/keys", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setKeyMessage(`✅ Successfully updated keys: ${result.updated.join(", ")}`);
      setShodanKey("");
      setAbuseipdbKey("");
      setVirusTotalKey("");
      setWpscanKey("");
      setNvdKey("");
    } catch (e) {
      setKeyMessage(`❌ Error updating keys: ${e.message}`);
    } finally {
      setUpdatingKeys(false);
    }
  }

  return (
    <>
      <PageTitle title="Admin Panel" subtitle="User management, scan monitoring, and system configuration." />
      {message && <p style={{ color: message.includes("Error") ? "#ffb4ab" : "#45dfa4", fontSize: 12, marginBottom: 16 }}>{message}</p>}

      <div style={{ display: "grid", gap: 24 }}>
        {/* Users Management */}
        <Card title="USERS MANAGEMENT" right={<span style={{ fontSize: 12, color: "var(--text-muted)" }}>{users.length} total</span>}>
          {loading ? (
            <p style={{ color: "var(--text-secondary)" }}>Loading...</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--ghost)" }}>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Email</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Name</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Organization</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Role</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Last Login</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} style={{ borderBottom: "1px solid var(--ghost)", ":hover": { background: "var(--surface-high)" } }}>
                      <td style={{ padding: 8, color: "var(--text)" }}>{u.email}</td>
                      <td style={{ padding: 8, color: "var(--text)" }}>{u.full_name || "—"}</td>
                      <td style={{ padding: 8, color: "var(--text)" }}>{u.organization || "—"}</td>
                      <td style={{ padding: 8 }}>
                        <Badge variant={u.role === "admin" ? "success" : "primary"}>{u.role?.toUpperCase() || "ANALYST"}</Badge>
                      </td>
                      <td style={{ padding: 8, color: "var(--text-secondary)", fontSize: 12 }}>
                        {u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never"}
                      </td>
                      <td style={{ padding: 8 }}>
                        <select
                          value={u.role || "analyst"}
                          onChange={(e) => updateUserRole(u.id, e.target.value)}
                          style={{
                            background: "var(--surface)",
                            color: "var(--text)",
                            border: "1px solid var(--ghost)",
                            padding: "4px 8px",
                            borderRadius: 4,
                            cursor: "pointer",
                            fontSize: 12,
                          }}
                        >
                          <option value="analyst">Analyst</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Scans Monitoring */}
        <Card title="RECENT SCANS" right={<span style={{ fontSize: 12, color: "var(--text-muted)" }}>{scans.length} total</span>}>
          {loading ? (
            <p style={{ color: "var(--text-secondary)" }}>Loading...</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--ghost)" }}>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Target</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Module</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>Timestamp</th>
                    <th style={{ textAlign: "left", padding: 8, color: "var(--text-muted)", fontWeight: 700 }}>User ID</th>
                  </tr>
                </thead>
                <tbody>
                  {scans.slice(0, 50).map((s, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid var(--ghost)" }}>
                      <td style={{ padding: 8, color: "var(--text)", wordBreak: "break-word" }}>{s.target || "—"}</td>
                      <td style={{ padding: 8, color: "var(--primary)", fontWeight: 600 }}>{s.module}</td>
                      <td style={{ padding: 8, color: "var(--text-secondary)", fontSize: 12 }}>
                        {new Date(s.timestamp).toLocaleString()}
                      </td>
                      <td style={{ padding: 8, color: "var(--text-muted)" }}>{s.user_id || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* API Keys Configuration */}
        <Card title="API KEYS CONFIGURATION" subtitle="Update VirusTotal, WPScan, and NVD API keys">
          {keyMessage && (
            <p style={{ color: keyMessage.includes("✅") ? "#45dfa4" : "#ffb4ab", fontSize: 12, marginBottom: 16 }}>
              {keyMessage}
            </p>
          )}
          <form onSubmit={(e) => e.preventDefault()} autoComplete="off">
            <div style={{ display: "grid", gap: 16 }}>
              <div>
                <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Shodan API Key
                </label>
                <input
                  type="password"
                  placeholder="Enter Shodan API key..."
                  value={shodanKey}
                  onChange={(e) => setShodanKey(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--surface)",
                    color: "var(--text)",
                    border: "1px solid var(--ghost)",
                    padding: 12,
                    borderRadius: 6,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  AbuseIPDB API Key
                </label>
                <input
                  type="password"
                  placeholder="Enter AbuseIPDB API key..."
                  value={abuseipdbKey}
                  onChange={(e) => setAbuseipdbKey(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--surface)",
                    color: "var(--text)",
                    border: "1px solid var(--ghost)",
                    padding: 12,
                    borderRadius: 6,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  VirusTotal API Key
                </label>
                <input
                  type="password"
                  placeholder="Enter VirusTotal API key..."
                  value={virusTotalKey}
                  onChange={(e) => setVirusTotalKey(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--surface)",
                    color: "var(--text)",
                    border: "1px solid var(--ghost)",
                    padding: 12,
                    borderRadius: 6,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  WPScan API Key
                </label>
                <input
                  type="password"
                  placeholder="Enter WPScan API key..."
                  value={wpscanKey}
                  onChange={(e) => setWpscanKey(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--surface)",
                    color: "var(--text)",
                    border: "1px solid var(--ghost)",
                    padding: 12,
                    borderRadius: 6,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  NVD API Key
                </label>
                <input
                  type="password"
                  placeholder="Enter NVD API key..."
                  value={nvdKey}
                  onChange={(e) => setNvdKey(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--surface)",
                    color: "var(--text)",
                    border: "1px solid var(--ghost)",
                    padding: 12,
                    borderRadius: 6,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <button
                onClick={saveApiKeys}
                disabled={updatingKeys || (!shodanKey && !abuseipdbKey && !virusTotalKey && !wpscanKey && !nvdKey)}
                style={{
                  background: "var(--primary)",
                  color: "white",
                  border: "none",
                  padding: 12,
                  borderRadius: 6,
                  fontWeight: 700,
                  cursor: updatingKeys || (!shodanKey && !abuseipdbKey && !virusTotalKey && !wpscanKey && !nvdKey) ? "not-allowed" : "pointer",
                  opacity: updatingKeys || (!shodanKey && !abuseipdbKey && !virusTotalKey && !wpscanKey && !nvdKey) ? 0.5 : 1,
                }}
              >
                {updatingKeys ? "Saving..." : "Save API Keys"}
              </button>
            </div>
          </form>
        </Card>
      </div>
    </>
  );
}

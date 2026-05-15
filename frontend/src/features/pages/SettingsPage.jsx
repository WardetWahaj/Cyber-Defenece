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

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "offline" }));
  }, [user]);

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



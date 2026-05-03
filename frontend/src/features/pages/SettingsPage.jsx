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
  }, []);

  async function refreshHealth() {
    try {
      const h = await api.health();
      setHealth(h);
    } catch {
      setHealth({ status: "offline" });
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

  return (
    <>
      <PageTitle title="Settings & API Integrations" subtitle="Connection status and environment diagnostics." />
      {message && <p style={{ color: "#45dfa4", fontSize: 12 }}>{message}</p>}
      {health?.status === "offline" && <p style={{ color: "#ffb4ab", fontSize: 12 }}>Backend health check is offline.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start", minHeight: "100vh" }}>
        <section style={{ display: "grid", gap: 24 }}>
          <Card title="API INTEGRATIONS" right={<Buttonish onClick={addProvider} />}>
            <div style={{ display: "grid", gap: 12 }}>
              {services.map(([name, state]) => (
                <div key={name} style={{ background: "#131b2e", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 16, fontWeight: 800 }}>{name}</div>
                    <div style={{ fontSize: 12, color: "#a0a0a0", marginTop: 4 }}>{name === "VirusTotal" ? "Aggregated antivirus results and reputation checks." : `Integration for ${name.toLowerCase()} telemetry.`}</div>
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
                <div style={{ width: 160, height: 160, borderRadius: "50%", background: "conic-gradient(#b4c5ff 0 83%, #2d3449 83% 100%)", display: "grid", placeItems: "center" }}>
                  <div style={{ width: 120, height: 120, borderRadius: "50%", background: "#131b2e", display: "grid", placeItems: "center", textAlign: "center" }}>
                    <div style={{ fontSize: 28, fontWeight: 800 }}>83%</div>
                    <div style={{ fontSize: 9, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.15em" }}>Operational</div>
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
            <div style={{ width: 90, height: 90, borderRadius: 18, border: "2px solid #b4c5ff", padding: 4, background: "#2d3449", display: "grid", placeItems: "center", fontSize: 36, fontWeight: 800, color: "#b4c5ff", flexShrink: 0 }}>
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, wordBreak: "break-word" }}>{user?.full_name || "User"}</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", wordBreak: "break-word" }}>{user?.email}</div>
            <div style={{ fontSize: 11, color: "#3B82F6", fontWeight: 800, letterSpacing: "0.16em" }}>
              {user?.organization || "ORGANIZATION"}
            </div>
            <div style={{ width: "100%", background: "#060d20", border: "1px solid rgba(67,70,85,0.15)", padding: 12, borderRadius: 6, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Account Status</span>
              <Badge variant="success">ACTIVE</Badge>
            </div>
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

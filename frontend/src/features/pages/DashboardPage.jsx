import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/ui/Card";
import PageTitle from "../../components/ui/PageTitle";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { api } from "../../lib/api";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [d, h] = await Promise.all([api.dashboard(), api.history(10)]);
        setDashboard(d);
        setHistory(h.items || []);
      } catch (e) {
        setError(String(e.message || e));
      }
    }
    load();
  }, []);

  const s = dashboard?.vulnerability_summary || { critical: 0, high: 0, medium: 0, low: 0 };
  const recent = dashboard?.recent_scan_history || [];
  const fullName = dashboard?.user?.full_name || "Analyst";

  function renderVulnDots(text) {
    const match = /([0-9]+)C\/([0-9]+)H\/([0-9]+)M/.exec(text || "0C/0H/0M");
    const critical = Number(match?.[1] || 0);
    const high = Number(match?.[2] || 0);
    const medium = Number(match?.[3] || 0);
    const low = 5 - Math.min(5, critical + high + medium);
    const dots = [];
    for (let i = 0; i < critical; i += 1) dots.push("#DC2626");
    for (let i = 0; i < high; i += 1) dots.push("#EF4444");
    for (let i = 0; i < medium; i += 1) dots.push("#FBBF24");
    for (let i = 0; i < low; i += 1) dots.push("#424754");
    return dots.slice(0, 5);
  }

  async function exportReport() {
    setExporting(true);
    setError("");
    try {
      const target = recent[0]?.target_asset || "example.com";
      const payload = await api.report({
        org_name: "CyberDefence SOC",
        target,
        author: "Dashboard Export",
        include_pdf: true,
      });

      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const href = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = href;
      a.download = `dashboard_report_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(href);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setExporting(false);
    }
  }

  return (
    <>
      <PageTitle 
        title="Dashboard" 
        subtitle={`Welcome back, ${fullName}`}
      />
      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <p style={{ color: "#ffb4ab", fontSize: 13, margin: 0 }}>{error}</p>
          <button 
            onClick={() => { setError(""); window.location.reload(); }}
            style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid var(--surface-high)", background: "var(--surface)", color: "var(--primary)", cursor: "pointer", fontSize: 12, whiteSpace: "nowrap" }}
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-4 page-section">
        {dashboard ? (
          <>
            <Card title="Critical Threats"><div className="kpi-value">{s.critical}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Immediate Action Required</div></Card>
            <Card title="High Risk"><div className="kpi-value">{s.high}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Assessing Propagation</div></Card>
            <Card title="Medium Alerts"><div className="kpi-value">{s.medium}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Routine Monitoring</div></Card>
            <Card title="Low Priority"><div className="kpi-value">{s.low}</div><div style={{ color: "var(--success)", fontSize: 11, fontWeight: 700 }}>Stable</div></Card>
          </>
        ) : (
          <>
            <Card title="Critical Threats"><Skeleton height={40} style={{ marginTop: 8 }} /></Card>
            <Card title="High Risk"><Skeleton height={40} style={{ marginTop: 8 }} /></Card>
            <Card title="Medium Alerts"><Skeleton height={40} style={{ marginTop: 8 }} /></Card>
            <Card title="Low Priority"><Skeleton height={40} style={{ marginTop: 8 }} /></Card>
          </>
        )}
      </div>

      <div className="grid grid-2 page-section">
        <Card title="Security Posture Score">
          {dashboard ? (
            <div style={{ display: "grid", placeItems: "center", minHeight: 250 }}>
              <div style={{ position: "relative", width: 180, height: 180, borderRadius: "50%", background: "conic-gradient(var(--primary) 0 78%, var(--surface-highest) 78% 100%)", display: "grid", placeItems: "center" }}>
                <div style={{ width: 132, height: 132, borderRadius: "50%", background: "var(--surface)", display: "grid", placeItems: "center", textAlign: "center" }}>
                  <div style={{ fontSize: 40, fontWeight: 800, lineHeight: 1 }}>{dashboard?.security_score ?? 0}<span style={{ fontSize: 18, color: "var(--text-muted)" }}>/100</span></div>
                  <div style={{ marginTop: 6, color: "var(--success)", fontSize: 11, fontWeight: 800, letterSpacing: "0.12em" }}>ACCEPTABLE</div>
                </div>
              </div>
              <p style={{ marginTop: 16, color: "var(--text-muted)", textAlign: "center", maxWidth: 240, fontSize: 12 }}>System security is currently within operational threshold. Recommend patching CVE-2024-8831.</p>
            </div>
          ) : (
            <div style={{ display: "grid", placeItems: "center", minHeight: 250 }}>
              <Skeleton width={180} height={180} style={{ borderRadius: "50%" }} />
            </div>
          )}
        </Card>

        <Card title="Live Data Sources" right={dashboard ? <Badge variant="success">SYSTEM LIVE</Badge> : undefined}>
          {dashboard ? (
            <div className="grid grid-2">
              {Object.entries(dashboard?.data_sources || {}).map(([name, connected]) => (
                <div key={name} style={{ background: "var(--surface-high)", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 12, fontWeight: 700 }}>{name}</span>
                  <Badge variant={connected ? "success" : "warning"}>{connected ? "CONNECTED" : "OFFLINE"}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} style={{ background: "var(--surface-high)", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: 12 }}>
                  <Skeleton height={20} />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid page-section" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        <button className="btn btn-primary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/scan/live")}>AUTO SCAN</button>
        <button className="btn btn-secondary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/scan/new")}>CUSTOM SCAN</button>
        <button className="btn btn-secondary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/reports/history")}>VIEW HISTORY</button>
      </div>

      <Card title="Recent Scan History" right={dashboard ? <button className="btn btn-secondary" onClick={exportReport} disabled={exporting}>{exporting ? "Exporting..." : "Export Report"}</button> : undefined} className="page-section">
        {dashboard ? (
          <table className="table">
            <thead>
              <tr>
                <th>TARGET ASSET</th>
                <th>TIMESTAMP</th>
                <th style={{ textAlign: "center" }}>SCORE</th>
                <th style={{ textAlign: "center" }}>VULNS</th>
                <th>STATUS</th>
                <th style={{ textAlign: "right" }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {recent.slice(0, 3).map((row, index) => (
                <tr 
                  key={row.id}
                  style={{ cursor: "pointer", transition: "background 0.2s" }}
                  onClick={() => navigate("/reports/history")}
                  onMouseEnter={(e) => e.currentTarget.style.background = "rgba(59,130,246,0.06)"}
                  onMouseLeave={(e) => e.currentTarget.style.background = ""}
                >
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div style={{ width: 30, height: 30, borderRadius: 6, background: "var(--surface-high)", display: "grid", placeItems: "center" }}>▪</div>
                      <div>
                        <div style={{ fontWeight: 700 }}>{row.target_asset}</div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{row.module}</div>
                      </div>
                    </div>
                  </td>
                  <td>{row.timestamp}</td>
                  <td style={{ textAlign: "center" }}><span className="badge" style={{ background: "rgba(59,130,246,0.12)", color: "var(--primary)" }}>{row.score}</span></td>
                  <td style={{ textAlign: "center" }}>
                    <div style={{ display: "inline-flex", gap: 4 }}>
                      {renderVulnDots(row.vulns).map((color, idx) => (
                        <span key={`${row.id}-${idx}`} style={{ width: 8, height: 8, borderRadius: 999, background: color, display: "inline-block" }} />
                      ))}
                    </div>
                  </td>
                  <td><Badge variant={index === 1 ? "info" : "success"}>{index === 1 ? "PROCESSING" : row.status}</Badge></td>
                  <td style={{ textAlign: "right", color: "var(--primary)", fontWeight: 700 }}>
                    <span onClick={(e) => {
                      e.stopPropagation();
                      navigate("/reports/history");
                    }} style={{ cursor: "pointer" }}>
                      open_in_new
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 12, borderBottom: "1px solid rgba(67,70,85,0.15)" }}>
                <div style={{ flex: 1 }}><Skeleton height={16} width="60%" /></div>
                <div style={{ flex: 1 }}><Skeleton height={16} width="70%" /></div>
                <div style={{ flex: 0.5 }}><Skeleton height={16} width="50%" /></div>
                <div style={{ flex: 0.5 }}><Skeleton height={16} width="40%" /></div>
                <div style={{ flex: 0.5 }}><Skeleton height={16} width="45%" /></div>
                <div style={{ flex: 0.3 }}><Skeleton height={16} width="30%" /></div>
              </div>
            ))}
          </div>
        )}
        {dashboard && recent.length === 0 && (
          <div style={{ textAlign: "center", padding: "20px", color: "var(--text-muted)" }}>
            No scans found. Start your first scan to see results here.
          </div>
        )}
      </Card>

      {history.length > 0 && <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>📊 Your recent scans • Showing {recent.slice(0, 3).length} of {recent.length} total scans</p>}
    </>
  );
}

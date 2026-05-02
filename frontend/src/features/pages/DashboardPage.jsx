import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/ui/Card";
import PageTitle from "../../components/ui/PageTitle";
import Badge from "../../components/ui/Badge";
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
        title="Landing Dashboard" 
        subtitle={`Welcome back, ${fullName}`}
      />
      {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}

      <div className="grid grid-4 page-section">
        <Card title="Critical Threats"><div className="kpi-value">{s.critical}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Immediate Action Required</div></Card>
        <Card title="High Risk"><div className="kpi-value">{s.high}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Assessing Propagation</div></Card>
        <Card title="Medium Alerts"><div className="kpi-value">{s.medium}</div><div style={{ color: "var(--text-muted)", fontSize: 11 }}>Routine Monitoring</div></Card>
        <Card title="Low Priority"><div className="kpi-value">{s.low}</div><div style={{ color: "#45dfa4", fontSize: 11, fontWeight: 700 }}>Stable</div></Card>
      </div>

      <div className="grid grid-2 page-section">
        <Card title="Security Posture Score">
          <div style={{ display: "grid", placeItems: "center", minHeight: 250 }}>
            <div style={{ position: "relative", width: 180, height: 180, borderRadius: "50%", background: "conic-gradient(#3B82F6 0 78%, #2d3449 78% 100%)", display: "grid", placeItems: "center" }}>
              <div style={{ width: 132, height: 132, borderRadius: "50%", background: "#0b1326", display: "grid", placeItems: "center", textAlign: "center" }}>
                <div style={{ fontSize: 40, fontWeight: 800, lineHeight: 1 }}>{dashboard?.security_score ?? 0}<span style={{ fontSize: 18, color: "var(--text-muted)" }}>/100</span></div>
                <div style={{ marginTop: 6, color: "#45dfa4", fontSize: 11, fontWeight: 800, letterSpacing: "0.12em" }}>ACCEPTABLE</div>
              </div>
            </div>
            <p style={{ marginTop: 16, color: "var(--text-muted)", textAlign: "center", maxWidth: 240, fontSize: 12 }}>System security is currently within operational threshold. Recommend patching CVE-2024-8831.</p>
          </div>
        </Card>

        <Card title="Live Data Sources" right={<Badge variant="success">SYSTEM LIVE</Badge>}>
          <div className="grid grid-2">
            {Object.entries(dashboard?.data_sources || {}).map(([name, connected]) => (
              <div key={name} style={{ background: "#171f33", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 700 }}>{name}</span>
                <Badge variant={connected ? "success" : "warning"}>{connected ? "CONNECTED" : "OFFLINE"}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid page-section" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        <button className="btn btn-primary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/scan/live")}>AUTO SCAN</button>
        <button className="btn btn-secondary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/scan/new")}>CUSTOM SCAN</button>
        <button className="btn btn-secondary" style={{ height: 100, fontSize: 13 }} onClick={() => navigate("/reports/history")}>VIEW HISTORY</button>
      </div>

      <Card title="Recent Scan History" right={<button className="btn btn-secondary" onClick={exportReport} disabled={exporting}>{exporting ? "Exporting..." : "Export Report"}</button>} className="page-section">
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
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(59,130,246,0.08)"}
                onMouseLeave={(e) => e.currentTarget.style.background = ""}
              >
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 30, height: 30, borderRadius: 6, background: "#222a3d", display: "grid", placeItems: "center" }}>▪</div>
                    <div>
                      <div style={{ fontWeight: 700 }}>{row.target_asset}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{row.module}</div>
                    </div>
                  </div>
                </td>
                <td>{row.timestamp}</td>
                <td style={{ textAlign: "center" }}><span className="badge" style={{ background: "rgba(59,130,246,0.16)", color: "#b4c5ff" }}>{row.score}</span></td>
                <td style={{ textAlign: "center" }}>
                  <div style={{ display: "inline-flex", gap: 4 }}>
                    {renderVulnDots(row.vulns).map((color, idx) => (
                      <span key={`${row.id}-${idx}`} style={{ width: 8, height: 8, borderRadius: 999, background: color, display: "inline-block" }} />
                    ))}
                  </div>
                </td>
                <td><Badge variant={index === 1 ? "info" : "success"}>{index === 1 ? "PROCESSING" : row.status}</Badge></td>
                <td style={{ textAlign: "right", color: "#3B82F6", fontWeight: 700 }}>
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
        {recent.length === 0 && (
          <div style={{ textAlign: "center", padding: "20px", color: "var(--text-muted)" }}>
            No scans found. Start your first scan to see results here.
          </div>
        )}
      </Card>

      {history.length > 0 && <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>📊 Your recent scans • Showing {recent.slice(0, 3).length} of {recent.length} total scans</p>}
    </>
  );
}

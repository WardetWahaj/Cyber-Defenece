import { useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { api } from "../../lib/api";

export default function SiemPage() {
  const [target, setTarget] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      setData(await api.siem(target));
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  return (
    <>
      <PageTitle title="SIEM Threat Analysis" subtitle="Event severity and attack pattern analysis from logs." />
      <Card title="Run SIEM Analysis" className="page-section">
        <div style={{ display: "flex", gap: 8 }}>
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="target label or domain" style={{ flex: 1, background: "var(--surface-high)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 10, borderRadius: 6 }} />
          <Button onClick={run} disabled={!target}>Analyze</Button>
        </div>
      </Card>
      {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}
      {data && (
        <>
          <div className="grid grid-4 page-section">
            <Card title="Critical"><div className="kpi-value">{data.critical || 0}</div></Card>
            <Card title="High"><div className="kpi-value">{data.high || 0}</div></Card>
            <Card title="Medium"><div className="kpi-value">{data.medium || 0}</div></Card>
            <Card title="Events"><div className="kpi-value">{data.events || 0}</div></Card>
          </div>

          <Card title="ACTIVE INCIDENT" right={<Badge variant="danger">ACTIVE</Badge>} className="page-section">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-muted)" }}>Targeting: Auth-Gateway-v4</div>
                <div style={{ fontSize: 24, fontWeight: 800, marginTop: 6 }}>Brute Force Attempt</div>
                <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>Moscow Region, RU · Cluster: RU-INET-241 · Duration: 04:12m</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.14em" }}>Current Vector Intensity</div>
                <div style={{ display: "flex", gap: 4, marginTop: 8, justifyContent: "end" }}>
                  {[1, 1, 1, 1, 0.3].map((alpha, index) => (
                    <div key={index} style={{ width: 6, height: 26, borderRadius: 999, background: `rgba(239,68,68,${alpha})` }} />
                  ))}
                </div>
              </div>
            </div>
          </Card>

          <div className="grid grid-2 page-section">
            <Card title="ATTACK PATTERNS DETECTED" right={<span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>LAST 24H</span>}>
              {Object.entries(data.patterns || {}).map(([name, count]) => (
                <div key={name} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                    <span>{name}</span>
                    <strong>{count}</strong>
                  </div>
                  <div style={{ height: 4, background: "var(--surface-high)", borderRadius: 999, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${Math.min(100, Number(count) || 0)}%`, background: "#3B82F6" }} />
                  </div>
                </div>
              ))}
            </Card>

            <Card title="TOP ATTACKING IPS">
              <table className="table">
                <thead>
                  <tr>
                    <th>SOURCE IP</th>
                    <th>GEOLOCATION</th>
                    <th style={{ textAlign: "right" }}>RISK LEVEL</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.top_ips || []).slice(0, 8).map((ip, idx) => (
                    <tr key={`${ip.ip}-${idx}`}>
                      <td>{ip.ip}</td>
                      <td>{ip.country || "Unknown"}</td>
                      <td style={{ textAlign: "right" }}>
                        <span className="badge" style={{ background: "rgba(220,38,38,0.16)", color: "#ffb4ab" }}>{ip.risk || "7.5/10"}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>

          <Card title="ACTIONABLE INTELLIGENCE" className="page-section">
            <div className="grid grid-2" style={{ gap: 16 }}>
              <div style={{ display: "grid", gap: 10 }}>
                <div><strong>Block Known Aggressors</strong><div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Blacklist Moscow subnet 185.156.72.0/24 immediately.</div></div>
                <div><strong>Enable Forced CAPTCHA</strong><div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Apply to all login attempts from RU/CN regions for 12 hours.</div></div>
              </div>
              <div style={{ display: "grid", gap: 10 }}>
                <div><strong>Flush Session Cache</strong><div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Clear auth tokens for accounts with &gt;5 failed attempts in 60s.</div></div>
                <div><strong>Trigger Forensics</strong><div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Initiate full packet capture on Node-Alpha for deep traffic analysis.</div></div>
              </div>
            </div>
          </Card>
        </>
      )}
    </>
  );
}

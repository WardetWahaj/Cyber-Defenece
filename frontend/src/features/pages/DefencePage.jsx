import { useState, useRef } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { api } from "../../lib/api";

export default function DefencePage() {
  const [target, setTarget] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [exporting, setExporting] = useState(null);
  const intervalRef = useRef(null);

  const modulesInfo = {
    headers: { label: "Security Headers Check", duration: 1500 },
    ssl: { label: "SSL/TLS Configuration", duration: 2000 },
    security: { label: "Security Policy Analysis", duration: 1200 },
  };

  async function run() {
    setLoading(true);
    setError("");
    setProgress(0);
    
    // Clear any existing interval
    if (intervalRef.current) clearInterval(intervalRef.current);
    
    // Simulate progress
    intervalRef.current = setInterval(() => {
      setProgress(prev => {
        if (prev >= 95) return 95;
        return prev + Math.random() * 15;
      });
    }, 500);
    
    try {
      const result = await api.defence(target);
      // Immediately clear the interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      // Small delay to flush pending state updates
      await new Promise(resolve => setTimeout(resolve, 50));
      setProgress(100);
      setData(result);
    } catch (e) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function downloadExport(format) {
    try {
      setExporting(format);
      const content = await api.exportVulnerabilities(target, format);
      const blob = new Blob([content], { type: format === "csv" ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `defence_report_${target.replace(/[^a-z0-9]/gi, "_")}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Export failed: ${err.message}`);
    } finally {
      setExporting(null);
    }
  }

  return (
    <>
      <PageTitle title="Defence Configuration Assessment" subtitle="14-point hardening review with weighted security score." />
      <Card title="Run Defence Assessment">
        <div style={{ display: "flex", gap: 8 }}>
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="https://target.example" style={{ flex: 1, background: "var(--surface-high)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 10, borderRadius: 6 }} />
          <Button onClick={run} disabled={!target || loading}>{loading ? "Assessing..." : "Assess"}</Button>
        </div>
      </Card>
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
      
      {loading && (
        <Card title="ASSESSMENT PROGRESS">
          <div style={{ display: "grid", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: "var(--text-muted)", letterSpacing: "0.05em" }}>DEFENCE ASSESSMENT</div>
              <div style={{ fontSize: 14, fontWeight: 900, color: "var(--primary)" }}>{Math.round(progress)}%</div>
            </div>
            
            <div style={{ width: "100%", height: 8, background: "var(--surface-high)", borderRadius: 4, overflow: "hidden", boxShadow: "inset 0 1px 3px rgba(0,0,0,0.2)" }}>
              <div style={{ 
                width: `${progress}%`, 
                height: "100%", 
                background: `linear-gradient(90deg, var(--primary) 0%, #60a5fa 50%, var(--primary) 100%)`,
                borderRadius: 4, 
                transition: "width 0.2s ease-out",
                boxShadow: "0 0 8px rgba(59, 130, 246, 0.5)"
              }} />
            </div>
            
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>ACTIVE ASSESSMENT MODULES</div>
              <div style={{ display: "grid", gap: 8 }}>
                {Object.entries(modulesInfo).map(([key, info], idx) => {
                  const moduleProgress = Math.min(100, Math.max(0, progress - (idx * 33)));
                  const isRunning = moduleProgress > 0 && moduleProgress < 100;
                  const isCompleted = moduleProgress === 100;
                  const status = isCompleted ? "✓" : isRunning ? "⟳" : "○";
                  const statusColor = isCompleted ? "#22c55e" : isRunning ? "var(--primary)" : "var(--text-muted)";
                  
                  return (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: 10, padding: 8, background: "var(--bg)", borderRadius: 6 }}>
                      <div style={{ fontSize: 16, color: statusColor, fontWeight: 800, minWidth: 20, textAlign: "center" }}>
                        {status}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
                          {info.label}
                        </div>
                        <div style={{ width: "100%", height: 4, background: "var(--surface-high)", borderRadius: 2, overflow: "hidden" }}>
                          <div style={{ 
                            width: `${moduleProgress}%`, 
                            height: "100%", 
                            background: statusColor,
                            transition: "width 0.3s ease-out"
                          }} />
                        </div>
                      </div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", minWidth: 30, textAlign: "right" }}>
                        {Math.round(moduleProgress)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div style={{ display: "grid", gap: 8, paddingTop: 8, borderTop: "1px solid var(--ghost)" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>TARGET BEING ASSESSED</div>
              <div style={{ fontSize: 13, color: "var(--text)", fontWeight: 600, wordBreak: "break-all", padding: 8, background: "var(--bg)", borderRadius: 4 }}>
                {target}
              </div>
            </div>
          </div>
        </Card>
      )}
      {data && (
        <>
          <div className="grid" style={{ gridTemplateColumns: "360px minmax(0, 1fr)", gap: 20, alignItems: "start" }}>
            <Card title="DEFENCE SCORE">
              <div style={{ display: "grid", placeItems: "center", padding: "10px 0 18px" }}>
                <div style={{ width: 180, height: 180, borderRadius: "50%", background: "conic-gradient(#3B82F6 0 72%, #2d3449 72% 100%)", display: "grid", placeItems: "center" }}>
                  <div style={{ width: 132, height: 132, borderRadius: "50%", background: "#0b1326", display: "grid", placeItems: "center", textAlign: "center" }}>
                    <div style={{ fontSize: 44, fontWeight: 800, lineHeight: 1 }}>{data.score}</div>
                    <div style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 800 }}>/100</div>
                  </div>
                </div>
                <div className="badge" style={{ marginTop: 16, background: "rgba(69,223,164,0.16)", color: "#45dfa4" }}>ACCEPTABLE</div>
              </div>
              <div className="grid grid-3" style={{ textAlign: "center", gap: 8 }}>
                <div><div style={{ fontSize: 22, fontWeight: 800, color: "#45dfa4" }}>{data.pass}</div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>PASS</div></div>
                <div><div style={{ fontSize: 22, fontWeight: 800, color: "#ffb4ab" }}>{data.fail}</div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>FAIL</div></div>
                <div><div style={{ fontSize: 22, fontWeight: 800, color: "#fbbf24" }}>{data.warn}</div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>WARN</div></div>
              </div>
            </Card>

            <div style={{ display: "grid", gap: 16 }}>
              <Card title="14-POINT DEFENCE CHECKLIST" right={
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Real-time monitoring active</span>
                  <button
                    onClick={() => downloadExport("csv")}
                    disabled={exporting === "csv"}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: "1px solid var(--primary)",
                      background: "transparent",
                      color: "var(--primary)",
                      cursor: "pointer",
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {exporting === "csv" ? "Exporting..." : "CSV"}
                  </button>
                  <button
                    onClick={() => downloadExport("json")}
                    disabled={exporting === "json"}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: "1px solid var(--primary)",
                      background: "transparent",
                      color: "var(--primary)",
                      cursor: "pointer",
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {exporting === "json" ? "Exporting..." : "JSON"}
                  </button>
                </div>
              }>
                <table className="table">
                  <thead>
                    <tr>
                      <th>CHECK NAME</th>
                      <th>REQUIREMENT</th>
                      <th>STATUS</th>
                      <th>DETAILS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.checks || []).map((check, idx) => (
                      <tr key={`${check.name}-${idx}`}>
                        <td>{check.name}</td>
                        <td>{check.requirement}</td>
                        <td>{check.status}</td>
                        <td>{check.details || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>

              <Card title="TACTICAL PRIORITIES">
                <div style={{ display: "grid", gap: 10 }}>
                  <div style={{ borderLeft: "3px solid #ffb4ab", paddingLeft: 10 }}><div style={{ fontSize: 12, fontWeight: 800, color: "#ffb4ab" }}>CRITICAL</div><div>Enforce MFA Global Policy</div></div>
                  <div style={{ borderLeft: "3px solid #ffb4ab", paddingLeft: 10 }}><div style={{ fontSize: 12, fontWeight: 800, color: "#ffb4ab" }}>CRITICAL</div><div>Update IAM Password Complexity</div></div>
                  <div style={{ borderLeft: "3px solid #fbbf24", paddingLeft: 10 }}><div style={{ fontSize: 12, fontWeight: 800, color: "#fbbf24" }}>MEDIUM</div><div>Rotate API Keys (&gt; 90 days)</div></div>
                  <div style={{ borderLeft: "3px solid #fbbf24", paddingLeft: 10 }}><div style={{ fontSize: 12, fontWeight: 800, color: "#fbbf24" }}>MEDIUM</div><div>Audit S3 Public Access Points</div></div>
                </div>
              </Card>
            </div>
          </div>
        </>
      )}
    </>
  );
}

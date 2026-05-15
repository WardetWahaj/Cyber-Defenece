import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PageTitle from "../../components/ui/PageTitle";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { api } from "../../lib/api";

export default function NewScanPage() {
  const navigate = useNavigate();
  const [target, setTarget] = useState("");
  const [scanMode, setScanMode] = useState("Quick");
  const [moduleFlags, setModuleFlags] = useState({
    portDiscovery: true,
    sslTls: true,
    assetMapping: true,
    dns: true,
    osint: false,
    sqli: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [currentModule, setCurrentModule] = useState("");
  const [modulesToScan, setModulesToScan] = useState([]);

  const modulesInfo = {
    recon: { label: "Reconnaissance", duration: 1500 },
    vulnerability: { label: "Vulnerability Assessment", duration: 2000 },
    defence: { label: "Defence Configuration", duration: 1200 },
    siem: { label: "SIEM Events Analysis", duration: 1000 },
    virustotal: { label: "Malware Reputation", duration: 800 },
  };

  function getModulesForMode() {
    if (scanMode === "Quick") return ["recon"];
    if (scanMode === "Standard") return ["recon", "vulnerability"];
    if (scanMode === "Comprehensive") return ["recon", "vulnerability", "defence", "siem", "virustotal"];

    const selected = [];
    if (moduleFlags.portDiscovery || moduleFlags.assetMapping || moduleFlags.dns) selected.push("recon");
    if (moduleFlags.sslTls) selected.push("defence");
    if (moduleFlags.osint || moduleFlags.sqli) selected.push("vulnerability");

    return Array.from(new Set(selected));
  }

  async function runScan() {
    setLoading(true);
    setError("");
    setProgress(0);
    setCurrentModule("");
    
    try {
      const modules = getModulesForMode();
      if (!modules.length) {
        throw new Error("Select at least one module in Custom mode.");
      }

      setModulesToScan(modules);

      // Start the scan and get job_id
      let jobResponse;
      if (scanMode === "Comprehensive") {
        jobResponse = await api.autoScan(target);
      } else {
        jobResponse = await api.customScan(target, modules);
      }

      const jobId = jobResponse.job_id;
      
      // Poll for job status every 3 seconds
      let completed = false;
      let result = null;
      
      while (!completed) {
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        try {
          const statusResponse = await api.scanStatus(jobId);
          setProgress(statusResponse.progress || 0);
          
          if (statusResponse.status === "completed") {
            completed = true;
            result = statusResponse.result;
            setResult(result);
          } else if (statusResponse.status === "failed") {
            throw new Error(statusResponse.error || "Scan failed");
          }
        } catch (e) {
          throw new Error(`Failed to fetch job status: ${e.message}`);
        }
      }

      setTimeout(() => {
        navigate(`/reports/pdf?target=${encodeURIComponent(target)}&autogen=1`);
      }, 800);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageTitle title="New Scan Modal" subtitle="Centered scan sheet with quick, standard, comprehensive, and custom modes." />

      <div style={{ minHeight: "72vh", display: "grid", placeItems: "center" }}>
        <div style={{ width: "min(500px, 100%)", background: "var(--surface-high)", backdropFilter: "blur(20px)", borderRadius: 8, border: "1px solid var(--ghost)", boxShadow: "0 24px 48px -12px rgba(0,0,0,0.6)", overflow: "hidden" }}>
          <div style={{ padding: 24, borderBottom: "1px solid var(--ghost)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>✨ NEW SECURITY SCAN</h2>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.16em", color: "var(--text-secondary)" }}>PROTOCOL V3-ALPHA</span>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-muted)", marginBottom: 8 }}>TARGET IDENTIFIER</div>
              <input
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="https://example.com or 192.168.1.1"
                style={{ width: "100%", background: "var(--surface)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 12, borderRadius: 6 }}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-muted)", marginBottom: 8 }}>SCAN MODE CONFIGURATION</div>
              <div className="grid grid-2" style={{ gap: 8 }}>
                {[
                  ["Quick", "L1 Recon • 5m"],
                  ["Standard", "L2 Audit • 15m"],
                  ["Comprehensive", "Full Depth • 1h+"],
                  ["Custom", "User Defined"],
                ].map(([title, desc]) => {
                  const active = scanMode === title;
                  return (
                    <button
                      key={title}
                      type="button"
                      onClick={() => setScanMode(title)}
                      style={{ background: active ? "var(--surface-high)" : "var(--surface)", border: `1px solid ${active ? "var(--primary)" : "var(--ghost)"}`, borderRadius: 6, padding: 12, textAlign: "left", color: "var(--text)", cursor: "pointer" }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 12, height: 12, borderRadius: 999, background: active ? "var(--primary)" : "transparent", border: `2px solid ${active ? "var(--primary)" : "var(--text-muted)"}` }} />
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 800, color: "var(--text)" }}>{title}</div>
                          <div style={{ fontSize: 10, color: "var(--text-muted)" }}>{desc}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-secondary)", marginBottom: 8 }}>ACTIVE ANALYTICS MODULES</div>
              <div style={{ background: "var(--surface)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 12 }}>
                <div className="grid grid-2" style={{ gap: 8 }}>
                  {[
                    ["portDiscovery", "Port Discovery"],
                    ["sslTls", "SSL/TLS"],
                    ["assetMapping", "Asset Mapping"],
                    ["dns", "DNS"],
                    ["osint", "OSINT"],
                    ["sqli", "SQLI"],
                  ].map(([key, label]) => (
                    <label key={label} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
                      <input
                        type="checkbox"
                        checked={Boolean(moduleFlags[key])}
                        onChange={(e) => setModuleFlags((prev) => ({ ...prev, [key]: e.target.checked }))}
                        style={{ accentColor: "#3B82F6" }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-muted)", marginBottom: 8 }}>API INTEGRATED INTELLIGENCE</div>
              <div style={{ display: "grid", gap: 8 }}>
                {["Shodan", "VirusTotal", "BinaryEdge", "HIBP", "Censys"].map((name) => (
                  <div key={name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0" }}>
                    <span style={{ fontSize: 13 }}>{name}</span>
                    <Badge variant="success">VERIFIED</Badge>
                  </div>
                ))}
              </div>
            </div>

            {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}
            
            {loading && (
              <div style={{ marginTop: 20, padding: 16, background: "var(--surface)", border: "1px solid var(--ghost)", borderRadius: 8, display: "grid", gap: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: "var(--text-muted)", letterSpacing: "0.05em" }}>SCAN PROGRESS</div>
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
                  <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>ACTIVE MODULES</div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {modulesToScan.map((module, idx) => {
                      const moduleProgress = Math.min(100, Math.max(0, progress - (idx * 20)));
                      const isRunning = moduleProgress > 0 && moduleProgress < 100;
                      const isCompleted = moduleProgress === 100;
                      const status = isCompleted ? "✓" : isRunning ? "⟳" : "○";
                      const statusColor = isCompleted ? "#22c55e" : isRunning ? "var(--primary)" : "var(--text-muted)";
                      
                      return (
                        <div key={module} style={{ display: "flex", alignItems: "center", gap: 10, padding: 8, background: "var(--bg)", borderRadius: 6 }}>
                          <div style={{ fontSize: 16, color: statusColor, fontWeight: 800, minWidth: 20, textAlign: "center" }}>
                            {status}
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
                              {modulesInfo[module]?.label || module}
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
                  <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>TARGET BEING SCANNED</div>
                  <div style={{ fontSize: 13, color: "var(--text)", fontWeight: 600, wordBreak: "break-all", padding: 8, background: "var(--bg)", borderRadius: 4 }}>
                    {target}
                  </div>
                </div>
              </div>
            )}
            
            {result?.results && (
              <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.12em" }}>SCAN SUMMARY</div>
                <div className="grid grid-2" style={{ gap: 8 }}>
                  <div style={{ background: "var(--surface)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 10 }}>
                    <div style={{ fontSize: 10, color: "var(--text-muted)" }}>VULNERABILITIES</div>
                    <div style={{ fontWeight: 800, color: "var(--text)" }}>{result.results?.vulnerability?.vulnerabilities?.length || 0} findings</div>
                  </div>
                  <div style={{ background: "var(--surface)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 10 }}>
                    <div style={{ fontSize: 10, color: "var(--text-muted)" }}>DEFENCE SCORE</div>
                    <div style={{ fontWeight: 800, color: "var(--text)" }}>{result.results?.defence?.score ?? "--"}/100</div>
                  </div>
                </div>

                {result.results?.shodan && !result.results.shodan.error && (
                  <div style={{ marginTop: 12, background: "var(--surface-high)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 12 }}>
                    <h4 style={{ margin: "0 0 12px 0", fontSize: 13, fontWeight: 800, color: "var(--text)" }}>🔎 Shodan Intelligence</h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>IP Address</span><br/><strong style={{ fontSize: 12 }}>{result.results.shodan.ip || result.results.shodan.resolved_ip || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Open Ports</span><br/><strong style={{ fontSize: 12, color: (result.results.shodan.ports?.length || 0) > 5 ? "var(--critical)" : "var(--success)" }}>{result.results.shodan.ports?.length || 0}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Vulnerabilities</span><br/><strong style={{ fontSize: 12, color: (result.results.shodan.total_vulns || 0) > 0 ? "var(--critical)" : "var(--success)" }}>{result.results.shodan.total_vulns || 0}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Organization</span><br/><strong style={{ fontSize: 12 }}>{result.results.shodan.organization || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>ISP</span><br/><strong style={{ fontSize: 12 }}>{result.results.shodan.isp || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Location</span><br/><strong style={{ fontSize: 12 }}>{result.results.shodan.city || "?"}, {result.results.shodan.country || "?"}</strong></div>
                    </div>
                    {result.results.shodan.services?.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <h5 style={{ margin: "0 0 8px 0", fontSize: 12, fontWeight: 700 }}>Services ({result.results.shodan.services.length})</h5>
                        <div style={{ maxHeight: 200, overflowY: "auto", fontSize: 11 }}>
                          <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                              <tr style={{ borderBottom: "1px solid var(--ghost)" }}>
                                <th style={{ padding: 4, textAlign: "left", fontWeight: 700 }}>Port</th>
                                <th style={{ padding: 4, textAlign: "left", fontWeight: 700 }}>Protocol</th>
                                <th style={{ padding: 4, textAlign: "left", fontWeight: 700 }}>Product</th>
                              </tr>
                            </thead>
                            <tbody>
                              {result.results.shodan.services.map((svc, i) => (
                                <tr key={i} style={{ borderBottom: "1px solid var(--ghost)" }}>
                                  <td style={{ padding: 4 }}><strong>{svc.port}</strong></td>
                                  <td style={{ padding: 4 }}>{svc.transport}</td>
                                  <td style={{ padding: 4 }}>{svc.product || "-"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    {result.results.shodan.vulns?.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <h5 style={{ margin: "0 0 6px 0", fontSize: 12, fontWeight: 700, color: "var(--critical)" }}>Known CVEs</h5>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {result.results.shodan.vulns.map((cve) => (
                            <span key={cve} style={{ background: "var(--critical)", color: "#fff", padding: "2px 6px", borderRadius: 3, fontSize: 10 }}>{cve}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {result.results?.abuseipdb && !result.results.abuseipdb.error && (
                  <div style={{ marginTop: 12, background: "var(--surface-high)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 12 }}>
                    <h4 style={{ margin: "0 0 12px 0", fontSize: 13, fontWeight: 800, color: "var(--text)" }}>⚠️ AbuseIPDB Reputation</h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
                      <div>
                        <span style={{ color: "var(--text-muted)", fontSize: 11 }}>Abuse Confidence</span><br/>
                        <strong style={{ fontSize: 16, color: (result.results.abuseipdb.abuse_confidence_score || 0) >= 50 ? "var(--critical)" : (result.results.abuseipdb.abuse_confidence_score || 0) > 0 ? "var(--medium)" : "var(--success)" }}>
                          {result.results.abuseipdb.abuse_confidence_score || 0}%
                        </strong>
                      </div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Total Reports</span><br/><strong style={{ fontSize: 12, color: (result.results.abuseipdb.total_reports || 0) > 0 ? "var(--critical)" : "var(--success)" }}>{result.results.abuseipdb.total_reports || 0}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>IP Address</span><br/><strong style={{ fontSize: 12 }}>{result.results.abuseipdb.resolved_ip || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>ISP</span><br/><strong style={{ fontSize: 12 }}>{result.results.abuseipdb.isp || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Country</span><br/><strong style={{ fontSize: 12 }}>{result.results.abuseipdb.country_code || "N/A"}</strong></div>
                      <div><span style={{ color: "var(--text-muted)", fontSize: 11 }}>Last Reported</span><br/><strong style={{ fontSize: 12 }}>{result.results.abuseipdb.last_reported_at || "Never"}</strong></div>
                    </div>
                  </div>
                )}
              </div>
            )}
            {result?.modules && <p style={{ color: "#45dfa4", fontSize: 12, marginTop: 8 }}>Completed modules: {result.modules.join(", ")}.</p>}
            {result && <p style={{ color: "#b4c5ff", fontSize: 12, marginTop: 8 }}>Scan completed. Redirecting to Full Report...</p>}
            {result && <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>{JSON.stringify({ mode: scanMode, ...(result.meta || {}), summary: result.results?.vulnerability?.summary || {} }, null, 2)}</pre>}
            {result && (
              <button className="btn btn-secondary" style={{ marginTop: 8 }} onClick={() => navigate(`/reports/pdf?target=${encodeURIComponent(target)}&autogen=1`)}>
                View Full Report
              </button>
            )}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 24, background: "var(--bg)" }}>
            <button className="btn btn-secondary" onClick={() => { setTarget(""); setResult(null); setError(""); setProgress(0); setCurrentModule(""); setModulesToScan([]); }}>Cancel</button>
            <Button onClick={runScan} disabled={loading || !target}>{loading ? "Scanning..." : "Run Scan →"}</Button>
          </div>
        </div>
      </div>
    </>
  );
}

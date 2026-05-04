import { useState } from "react";
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
    try {
      const modules = getModulesForMode();
      if (!modules.length) {
        throw new Error("Select at least one module in Custom mode.");
      }

      let data;
      if (scanMode === "Comprehensive") {
        data = await api.autoScan(target);
      } else {
        data = await api.customScan(target, modules);
      }

      setResult(data);
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
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", color: "var(--text-secondary)", marginBottom: 8 }}>API INTEGRATED INTELLIGENCE</div>
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
            {loading && <p style={{ color: "#b4c5ff", fontSize: 12 }}>Scan in progress... this can take up to a few minutes depending on target.</p>}
            {result?.results && (
              <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                <div style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 800, letterSpacing: "0.12em" }}>SCAN SUMMARY</div>
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

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 24, background: "#0b1326" }}>
            <button className="btn btn-secondary" onClick={() => { setTarget(""); setResult(null); setError(""); }}>Cancel</button>
            <Button onClick={runScan} disabled={loading || !target}>{loading ? "Scanning..." : "Run Scan →"}</Button>
          </div>
        </div>
      </div>
    </>
  );
}

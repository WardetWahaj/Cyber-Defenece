import { useState } from "react";
import Card from "../../components/ui/Card";
import PageTitle from "../../components/ui/PageTitle";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { api } from "../../lib/api";

export default function ShodanPage() {
  const [target, setTarget] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleScan(e) {
    e.preventDefault();
    if (!target.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.shodan(target.trim());
      setResult(data);
    } catch (err) {
      setError(err.message || "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageTitle title="Shodan Intelligence" subtitle="Internet-wide device and service discovery" />
      
      <Card>
        <form onSubmit={handleScan} style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Enter target domain or IP..."
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            style={{ flex: 1, minWidth: 220, padding: "10px 14px", background: "var(--surface-high)", color: "var(--text)", border: "1px solid var(--ghost)", borderRadius: 6 }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{ padding: "10px 24px", background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, cursor: loading ? "wait" : "pointer", opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "Scanning..." : "Scan with Shodan"}
          </button>
        </form>
      </Card>

      {error && (
        <Card>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <p style={{ color: "var(--critical)", fontSize: 13, margin: 0 }}>{error}</p>
            <button 
              onClick={() => { setError(""); window.location.reload(); }}
              style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid var(--surface-high)", background: "var(--surface)", color: "var(--primary)", cursor: "pointer", fontSize: 12, whiteSpace: "nowrap" }}
            >
              Retry
            </button>
          </div>
        </Card>
      )}

      {loading && (
        <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
          <Skeleton height={32} width="40%" />
          <Skeleton height={200} />
          <Skeleton height={200} />
          <Skeleton height={120} />
        </div>
      )}

      {result && !result.error && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginTop: 16 }}>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>IP Address</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{result.ip || result.resolved_ip || "N/A"}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Open Ports</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4, color: (result.ports?.length || 0) > 5 ? "var(--critical)" : "var(--success)" }}>{result.ports?.length || 0}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Vulnerabilities</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4, color: (result.total_vulns || 0) > 0 ? "var(--critical)" : "var(--success)" }}>{result.total_vulns || 0}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Location</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{result.city || "?"}, {result.country || "?"}</div>
            </Card>
          </div>

          <Card style={{ marginTop: 16 }}>
            <h3 style={{ marginBottom: 12 }}>Host Details</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {[
                  ["Organization", result.organization],
                  ["ISP", result.isp],
                  ["OS", result.os],
                  ["Ports", (result.ports || []).join(", ") || "None"],
                  ["Last Updated", result.last_update || "N/A"],
                ].map(([label, val]) => (
                  <tr key={label} style={{ borderBottom: "1px solid var(--ghost)" }}>
                    <td style={{ padding: "8px 12px", color: "var(--text-muted)", width: "30%" }}>{label}</td>
                    <td style={{ padding: "8px 12px" }}>{val || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {result.services?.length > 0 && (
            <Card style={{ marginTop: 16 }}>
              <h3 style={{ marginBottom: 12 }}>Services ({result.services.length})</h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--ghost)" }}>
                    <th style={{ padding: "8px 12px", textAlign: "left", color: "var(--text-muted)" }}>Port</th>
                    <th style={{ padding: "8px 12px", textAlign: "left", color: "var(--text-muted)" }}>Protocol</th>
                    <th style={{ padding: "8px 12px", textAlign: "left", color: "var(--text-muted)" }}>Product</th>
                    <th style={{ padding: "8px 12px", textAlign: "left", color: "var(--text-muted)" }}>Version</th>
                  </tr>
                </thead>
                <tbody>
                  {result.services.map((svc, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--ghost)" }}>
                      <td style={{ padding: "8px 12px", fontWeight: 600 }}>{svc.port}</td>
                      <td style={{ padding: "8px 12px" }}>{svc.transport}</td>
                      <td style={{ padding: "8px 12px" }}>{svc.product}</td>
                      <td style={{ padding: "8px 12px" }}>{svc.version || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          {result.vulns?.length > 0 && (
            <Card style={{ marginTop: 16 }}>
              <h3 style={{ marginBottom: 12, color: "var(--critical)" }}>Known Vulnerabilities ({result.vulns.length})</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {result.vulns.map((cve) => (
                  <Badge key={cve} variant="critical">{cve}</Badge>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {result?.error && (
        <Card>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <p style={{ color: "var(--critical)", fontSize: 13, margin: 0 }}>{result.error}</p>
            <button 
              onClick={() => { window.location.reload(); }}
              style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid var(--surface-high)", background: "var(--surface)", color: "var(--primary)", cursor: "pointer", fontSize: 12, whiteSpace: "nowrap" }}
            >
              Retry
            </button>
          </div>
        </Card>
      )}
    </>
  );
}

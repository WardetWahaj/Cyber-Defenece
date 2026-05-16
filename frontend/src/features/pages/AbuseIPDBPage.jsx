import { useState } from "react";
import Card from "../../components/ui/Card";
import PageTitle from "../../components/ui/PageTitle";
import Skeleton from "../../components/ui/Skeleton";
import { api } from "../../lib/api";

export default function AbuseIPDBPage() {
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
      const data = await api.abuseipdb(target.trim());
      setResult(data);
    } catch (err) {
      setError(err.message || "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  function getScoreColor(score) {
    if (score >= 75) return "var(--critical)";
    if (score >= 40) return "var(--medium)";
    return "var(--success)";
  }

  function getVerdict(score) {
    if (score >= 75) return "DANGEROUS — High abuse confidence";
    if (score >= 40) return "SUSPICIOUS — Moderate abuse reports";
    if (score > 0) return "LOW RISK — Minor abuse reports";
    return "CLEAN — No abuse reports";
  }

  return (
    <>
      <PageTitle title="AbuseIPDB Check" subtitle="IP reputation and abuse report analysis" />
      
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
            {loading ? "Checking..." : "Check IP Reputation"}
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
          <Card style={{ marginTop: 16, textAlign: "center", padding: 24 }}>
            <div style={{ fontSize: 14, color: "var(--text-muted)" }}>Abuse Confidence Score</div>
            <div style={{ fontSize: 48, fontWeight: 800, color: getScoreColor(result.abuse_confidence_score || 0), margin: "8px 0" }}>
              {result.abuse_confidence_score || 0}%
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: getScoreColor(result.abuse_confidence_score || 0) }}>
              {getVerdict(result.abuse_confidence_score || 0)}
            </div>
          </Card>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginTop: 16 }}>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Resolved IP</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{result.resolved_ip || "N/A"}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Total Reports</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4, color: (result.total_reports || 0) > 0 ? "var(--critical)" : "var(--success)" }}>{result.total_reports || 0}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Distinct Reporters</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{result.num_distinct_users || 0}</div>
            </Card>
            <Card>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Country</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{result.country_code || "N/A"}</div>
            </Card>
          </div>

          <Card style={{ marginTop: 16 }}>
            <h3 style={{ marginBottom: 12 }}>IP Details</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {[
                  ["ISP", result.isp],
                  ["Domain", result.domain],
                  ["Usage Type", result.usage_type],
                  ["Whitelisted", result.is_whitelisted ? "Yes" : "No"],
                  ["Public", result.is_public ? "Yes" : "No"],
                  ["Last Reported", result.last_reported_at || "Never"],
                ].map(([label, val]) => (
                  <tr key={label} style={{ borderBottom: "1px solid var(--ghost)" }}>
                    <td style={{ padding: "8px 12px", color: "var(--text-muted)", width: "30%" }}>{label}</td>
                    <td style={{ padding: "8px 12px" }}>{val || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
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

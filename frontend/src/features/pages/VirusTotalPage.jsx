import { useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { api } from "../../lib/api";

export default function VirusTotalPage() {
  const [target, setTarget] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      setData(await api.virustotal(target));
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  return (
    <>
      <PageTitle title="VirusTotal Reputation Report" subtitle="External threat reputation across 90+ engines." />
      <Card title="Reputation Check">
        <div style={{ display: "flex", gap: 8 }}>
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="example.com" style={{ flex: 1, background: "var(--surface-high)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 10, borderRadius: 6 }} />
          <Button onClick={run} disabled={!target}>Check</Button>
        </div>
      </Card>
      {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}
      {data && (
        <div className="grid grid-3">
          <Card title="Verdict"><Badge variant={data.malicious > 0 ? "danger" : "success"}>{data.malicious > 0 ? "Suspicious" : "Clean"}</Badge></Card>
          <Card title="Detections"><div className="kpi-value">{data.malicious || 0}</div></Card>
          <Card title="Total Engines"><div className="kpi-value">{data.total_engines || 0}</div></Card>
        </div>
      )}
    </>
  );
}

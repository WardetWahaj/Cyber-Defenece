import { useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { api } from "../../lib/api";

export default function DefencePage() {
  const [target, setTarget] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      setData(await api.defence(target));
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  return (
    <>
      <PageTitle title="Defence Configuration Assessment" subtitle="14-point hardening review with weighted security score." />
      <Card title="Run Defence Assessment">
        <div style={{ display: "flex", gap: 8 }}>
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="https://target.example" style={{ flex: 1, background: "var(--surface-high)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 10, borderRadius: 6 }} />
          <Button onClick={run} disabled={!target}>Assess</Button>
        </div>
      </Card>
      {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}
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
              <Card title="14-POINT DEFENCE CHECKLIST" right={<span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Real-time monitoring active</span>}>
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

import { useEffect, useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import { api } from "../../lib/api";

export default function ReportsHistoryPage() {
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [error, setError] = useState("");
  const [targetFilter, setTargetFilter] = useState("");
  const [minGrade, setMinGrade] = useState("ALL");

  function riskDots(item) {
    const results = item.results || {};
    const summary = results.summary || {};
    const critical = Number(summary.critical || 0);
    const high = Number(summary.high || 0);
    const medium = Number(summary.medium || 0);
    const score = Math.max(0, 100 - (critical * 15 + high * 6 + medium * 2));
    if (score >= 85) return { grade: "A-", text: "Low Risk", colors: ["#424754", "#424754", "#45dfa4", "#45dfa4", "#45dfa4"] };
    if (score >= 70) return { grade: "C+", text: "High Risk", colors: ["#424754", "#DC2626", "#DC2626", "#DC2626", "#DC2626"] };
    if (score >= 55) return { grade: "B", text: "Moderate", colors: ["#424754", "#424754", "#424754", "#F59E0B", "#F59E0B"] };
    return { grade: "F", text: "Critical Failure", colors: ["#DC2626", "#DC2626", "#DC2626", "#DC2626", "#DC2626"] };
  }

  useEffect(() => {
    async function load() {
      try {
        const data = await api.scanHistory(50);
        const rows = (data.scans || []).map(scan => ({
          id: scan.id,
          target: scan.target,
          module: scan.module,
          timestamp: scan.timestamp,
          results: scan.results
        }));
        setItems(rows);
        setFilteredItems(rows);
      } catch (e) {
        setError(String(e.message || e));
      }
    }
    load();
  }, []);

  function gradeRank(grade) {
    if (grade.startsWith("A")) return 4;
    if (grade.startsWith("B")) return 3;
    if (grade.startsWith("C")) return 2;
    if (grade.startsWith("D")) return 1;
    return 0;
  }

  function applyFilters() {
    const targetText = targetFilter.trim().toLowerCase();
    const minRank = minGrade === "ALL" ? -1 : gradeRank(minGrade);

    const next = items.filter((item) => {
      const targetOk = !targetText || String(item.target || "").toLowerCase().includes(targetText);
      const grade = riskDots(item).grade;
      const gradeOk = minRank < 0 || gradeRank(grade) >= minRank;
      return targetOk && gradeOk;
    });

    setFilteredItems(next);
  }

  return (
    <>
      <PageTitle title="Reports History" subtitle="Historical scans and generated artifacts." />
      {error && <p style={{ color: "#ffb4ab" }}>{error}</p>}

      <div className="grid grid-3 page-section">
        <Card title="TOTAL REPORTS">
          <div className="kpi-value">1,248</div>
          <div style={{ color: "#45dfa4", fontSize: 11, fontWeight: 700 }}>+12% from last month</div>
        </Card>
        <Card title="AVG SECURITY GRADE">
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <div className="kpi-value">B+</div>
            <div style={{ color: "var(--text-secondary)", fontSize: 18 }}>/ 88.4</div>
          </div>
          <div style={{ height: 6, background: "#222a3d", borderRadius: 999, overflow: "hidden", marginTop: 12 }}>
            <div style={{ width: "88%", height: "100%", background: "#b4c5ff" }} />
          </div>
        </Card>
        <Card title="VULNS FOUND">
          <div className="kpi-value" style={{ color: "#ffb4ab" }}>42</div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>8 Critical | 34 Moderate</div>
        </Card>
      </div>

      <div className="card page-section" style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "end" }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.14em", marginBottom: 6 }}>DATE RANGE</div>
            <div style={{ background: "#131b2e", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: "8px 12px", fontSize: 12 }}>Last 30 Days</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.14em", marginBottom: 6 }}>MIN. SCORE</div>
            <select value={minGrade} onChange={(e) => setMinGrade(e.target.value)} style={{ background: "#131b2e", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: "8px 12px", color: "var(--text)", fontSize: 12 }}>
              <option value="ALL">All</option>
              <option value="C">C or better</option>
              <option value="B">B or better</option>
              <option value="A">A only</option>
            </select>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.14em", marginBottom: 6 }}>TARGET DOMAIN</div>
            <input value={targetFilter} onChange={(e) => setTargetFilter(e.target.value)} placeholder="Search target..." style={{ background: "#131b2e", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: "8px 12px", color: "var(--text)" }} />
          </div>
        </div>
        <button className="btn btn-secondary" onClick={applyFilters}>Apply Filters</button>
      </div>

      <Card title="Archive">
        <table className="table">
          <thead>
            <tr>
              <th>REPORT ID</th>
              <th>TARGET ENTITY</th>
              <th>DATE</th>
              <th style={{ textAlign: "center" }}>SCORE</th>
              <th>RISK DISTRIBUTION</th>
              <th style={{ textAlign: "right" }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr key={item.id}>
                <td>{`RPT-2023-${String(item.id).padStart(4, "0")}`}</td>
                <td>
                  <div style={{ fontWeight: 700 }}>{item.target}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{item.module}</div>
                </td>
                <td>{item.timestamp}</td>
                <td style={{ textAlign: "center" }}>
                  <span className="badge" style={{ background: "rgba(59,130,246,0.16)", color: "#b4c5ff" }}>{riskDots(item).grade}</span>
                </td>
                <td>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    {riskDots(item).colors.map((color, idx) => (
                      <span key={`${item.id}-risk-${idx}`} style={{ width: 8, height: 8, borderRadius: 999, background: color, display: "inline-block" }} />
                    ))}
                    <span style={{ fontSize: 11, marginLeft: 8, color: "var(--text-secondary)" }}>{riskDots(item).text}</span>
                  </div>
                </td>
                <td style={{ textAlign: "right" }}>visibility download more_vert</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>Showing {filteredItems.length} of {items.length} records.</p>
    </>
  );
}

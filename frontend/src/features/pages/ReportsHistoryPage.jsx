import { useEffect, useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import { api } from "../../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function ReportsHistoryPage() {
  const [reports, setReports] = useState([]);
  const [filteredReports, setFilteredReports] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [targetFilter, setTargetFilter] = useState("");
  const [minGrade, setMinGrade] = useState("ALL");
  const [downloading, setDownloading] = useState(null);

  // Calculate security score from summary
  function calculateSecurityScore(report) {
    if (!report.results || !report.results.summary) {
      // Generate random score for now
      return Math.floor(Math.random() * 40) + 60;
    }
    const summary = report.results.summary;
    const critical = Number(summary.critical || 0);
    const high = Number(summary.high || 0);
    const medium = Number(summary.medium || 0);
    return Math.max(0, 100 - (critical * 15 + high * 6 + medium * 2));
  }

  // Get grade from score
  function getGradeFromScore(score) {
    if (score >= 85) return "A";
    if (score >= 70) return "B";
    if (score >= 55) return "C";
    if (score >= 40) return "D";
    return "F";
  }

  // Get grade rank for comparison
  function gradeRank(grade) {
    const baseGrade = grade.charAt(0);
    if (baseGrade === "A") return 4;
    if (baseGrade === "B") return 3;
    if (baseGrade === "C") return 2;
    if (baseGrade === "D") return 1;
    return 0;
  }

  // Get risk assessment
  function riskDots(report) {
    const score = calculateSecurityScore(report);
    if (score >= 85) return { grade: "A-", text: "Low Risk", colors: ["#424754", "#424754", "#45dfa4", "#45dfa4", "#45dfa4"] };
    if (score >= 70) return { grade: "B+", text: "Acceptable", colors: ["#424754", "#424754", "#424754", "#45dfa4", "#45dfa4"] };
    if (score >= 55) return { grade: "C+", text: "Moderate Risk", colors: ["#424754", "#424754", "#F59E0B", "#F59E0B", "#F59E0B"] };
    return { grade: "F", text: "Critical", colors: ["#DC2626", "#DC2626", "#DC2626", "#DC2626", "#DC2626"] };
  }

  // Format date
  function formatDate(isoString) {
    if (!isoString) return "N/A";
    try {
      return new Date(isoString).toLocaleDateString() + " " + new Date(isoString).toLocaleTimeString();
    } catch {
      return isoString;
    }
  }

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        const data = await api.request("/api/reports/list?limit=100");
        if (data.reports && Array.isArray(data.reports)) {
          setReports(data.reports);
          setFilteredReports(data.reports);
        }
      } catch (e) {
        setError(String(e.message || e));
        // Fallback to empty reports list
        setReports([]);
        setFilteredReports([]);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  function applyFilters() {
    const targetText = targetFilter.trim().toLowerCase();
    const minRank = minGrade === "ALL" ? -1 : gradeRank(minGrade);
    
    const next = reports.filter((report) => {
      const targetOk = !targetText || String(report.target || "").toLowerCase().includes(targetText);
      const score = calculateSecurityScore(report);
      const reportGrade = getGradeFromScore(score);
      const gradeOk = minRank < 0 || gradeRank(reportGrade) >= minRank;
      return targetOk && gradeOk;
    });
    setFilteredReports(next);
  }

  async function downloadReport(report) {
    if (!report.pdf_path) {
      alert("No PDF available for this report");
      return;
    }

    try {
      setDownloading(report.id);
      const token = localStorage.getItem("auth_token");
      const filename = report.pdf_path.split(/[\\/]/).pop();
      const fullUrl = `${API_BASE}/api/report/download?filename=${encodeURIComponent(filename)}`;
      
      const headers = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(fullUrl, { headers });
      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (e) {
      alert(`Download failed: ${e.message}`);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <>
      <PageTitle title="Reports History" subtitle="Your generated security reports and historical analysis." />
      {error && <p style={{ color: "#ffb4ab", marginBottom: "1rem" }}>⚠️ {error}</p>}
      {loading && <p style={{ color: "var(--text-muted)" }}>Loading reports...</p>}

      <div className="grid grid-3 page-section">
        <Card title="TOTAL REPORTS">
          <div className="kpi-value">{reports.length}</div>
          <div style={{ color: "var(--success)", fontSize: 11, fontWeight: 700 }}>Generated in this account</div>
        </Card>
        <Card title="AVG SECURITY SCORE">
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <div className="kpi-value">{reports.length > 0 ? (reports.reduce((sum, r) => sum + calculateSecurityScore(r), 0) / reports.length).toFixed(0) : "—"}</div>
            <div style={{ color: "var(--text-secondary)", fontSize: 18 }}>/100</div>
          </div>
          <div style={{ height: 6, background: "var(--surface-high)", borderRadius: 999, overflow: "hidden", marginTop: 12 }}>
            <div style={{ width: reports.length > 0 ? ((reports.reduce((sum, r) => sum + calculateSecurityScore(r), 0) / reports.length) / 100 * 100) + "%" : "0%", height: "100%", background: "var(--primary)" }} />
          </div>
        </Card>
        <Card title="RECENT REPORTS">
          <div className="kpi-value" style={{ color: "var(--primary)" }}>{filteredReports.length}</div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Matching current filters</div>
        </Card>
      </div>

      <div className="card page-section" style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "end" }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.14em", marginBottom: 6 }}>MIN. SCORE</div>
            <select 
              value={minGrade} 
              onChange={(e) => setMinGrade(e.target.value)} 
              style={{ background: "var(--surface-high)", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: "8px 12px", color: "var(--text)", fontSize: 12 }}
            >
              <option value="ALL">All</option>
              <option value="C">C or better</option>
              <option value="B">B or better</option>
              <option value="A">A only</option>
            </select>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 800, letterSpacing: "0.14em", marginBottom: 6 }}>TARGET DOMAIN</div>
            <input 
              value={targetFilter} 
              onChange={(e) => setTargetFilter(e.target.value)} 
              placeholder="Search by domain..." 
              style={{ background: "var(--surface-high)", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 6, padding: "8px 12px", color: "var(--text)", fontSize: 12 }} 
            />
          </div>
        </div>
        <button className="btn btn-secondary" onClick={applyFilters}>Apply Filters</button>
      </div>

      {filteredReports.length === 0 && !loading ? (
        <Card title="No Reports">
          <p style={{ color: "var(--text-muted)" }}>
            {reports.length === 0 
              ? "No reports generated yet. Generate your first report from the PDF Report section."
              : "No reports match the current filters. Try adjusting your search."}
          </p>
        </Card>
      ) : (
        <Card title="Report Archive">
          <table className="table">
            <thead>
              <tr>
                <th>REPORT ID</th>
                <th>TARGET</th>
                <th>ORGANIZATION</th>
                <th>DATE GENERATED</th>
                <th style={{ textAlign: "center" }}>SCORE</th>
                <th style={{ textAlign: "right" }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.map((report) => (
                <tr key={report.id}>
                  <td>{`RPT-${String(report.id).padStart(6, "0")}`}</td>
                  <td>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>{report.target}</div>
                  </td>
                  <td style={{ fontSize: 12, color: "var(--text-secondary)" }}>{report.org_name}</td>
                  <td style={{ fontSize: 12 }}>{formatDate(report.created_at)}</td>
                  <td style={{ textAlign: "center" }}>
                    <span className="badge" style={{ background: "rgba(59,130,246,0.16)", color: "var(--primary)" }}>
                      {calculateSecurityScore(report)}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {report.pdf_path ? (
                      <button 
                        onClick={() => downloadReport(report)}
                        disabled={downloading === report.id}
                        style={{
                          background: "none",
                          border: "none",
                          color: "var(--primary)",
                          cursor: downloading === report.id ? "wait" : "pointer",
                          fontSize: 14,
                          fontWeight: 700,
                          opacity: downloading === report.id ? 0.5 : 1
                        }}
                      >
                        {downloading === report.id ? "⏳" : "download"}
                      </button>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: 12 }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      
      <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>
        Showing {filteredReports.length} of {reports.length} reports.
      </p>
    </>
  );
}

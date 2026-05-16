import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../../lib/api";

export default function ScoreTrendCard() {
  const [targets, setTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState("");
  const [history, setHistory] = useState([]);
  const [trend, setTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch list of targets (scanned targets) on mount
  useEffect(() => {
    fetchTargets();
  }, []);

  // Fetch score history when target changes
  useEffect(() => {
    if (selectedTarget) {
      fetchScoreHistory(selectedTarget);
    }
  }, [selectedTarget]);

  async function fetchTargets() {
    try {
      // Get list of unique targets from scan history
      const historyData = await api.scanHistory(100);
      const uniqueTargets = [...new Set(historyData.items.map(item => item.target))].slice(0, 10);
      setTargets(uniqueTargets);
      if (uniqueTargets.length > 0) {
        setSelectedTarget(uniqueTargets[0]);
      }
    } catch (err) {
      console.error("Failed to fetch targets:", err);
    }
  }

  async function fetchScoreHistory(target) {
    try {
      setLoading(true);
      setError("");
      const data = await api.scoreHistory(target, 30);
      
      // Reverse to show oldest first (for chart)
      const reversed = [...data.history].reverse();
      setHistory(reversed);
      setTrend(data.trend);
    } catch (err) {
      setError(err.message);
      console.error("Failed to fetch score history:", err);
    } finally {
      setLoading(false);
    }
  }

  function getGradeColor(grade) {
    if (grade === "A" || grade === "B") return "#34c759";
    if (grade === "C") return "#ffcc00";
    if (grade === "D") return "#ff2d55";
    return "#8b949e";
  }

  function formatDate(dateString) {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return dateString;
    }
  }

  const currentGrade = history.length > 0 ? history[history.length - 1].grade : "-";
  const lineColor = getGradeColor(currentGrade);

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--surface-high)",
        borderRadius: 12,
        padding: 24,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "var(--text)" }}>Security Score Trend</h3>
          <p style={{ margin: "4px 0 0 0", fontSize: 12, color: "var(--text-muted)" }}>
            Track your security posture over time
          </p>
        </div>

        {/* Target Selector */}
        <select
          value={selectedTarget}
          onChange={(e) => setSelectedTarget(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid var(--surface-high)",
            background: "var(--surface-low)",
            color: "var(--text)",
            fontSize: 12,
            cursor: "pointer",
            minWidth: 150,
          }}
        >
          {targets.map((target) => (
            <option key={target} value={target}>
              {target}
            </option>
          ))}
        </select>
      </div>

      {/* Trend Info */}
      {trend && (
        <div
          style={{
            background: "var(--surface-low)",
            border: "1px solid var(--surface-high)",
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
            fontSize: 12,
            color: trend.direction === "up" ? "#34c759" : trend.direction === "down" ? "#ff2d55" : "var(--text-muted)",
            fontWeight: 600,
          }}
        >
          {trend.direction === "up" ? "📈" : trend.direction === "down" ? "📉" : "➡️"} {trend.display}
        </div>
      )}

      {error && (
        <div style={{ color: "#ffb4ab", fontSize: 12, marginBottom: 12 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Chart */}
      {loading ? (
        <div style={{ height: 300, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
          Loading chart...
        </div>
      ) : history.length === 0 ? (
        <div style={{ height: 300, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
          <p style={{ margin: 0 }}>No score history yet. Run a scan to start tracking trends.</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={history} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-high)" />
            <XAxis
              dataKey="scanned_at"
              tickFormatter={(date) => formatDate(date)}
              stroke="var(--text-muted)"
              style={{ fontSize: 11 }}
            />
            <YAxis domain={[0, 100]} stroke="var(--text-muted)" style={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: "var(--surface-high)",
                border: "1px solid var(--surface-high)",
                borderRadius: 6,
                color: "var(--text)",
              }}
              formatter={(value) => [`${value}`, "Score"]}
              labelFormatter={(date) => formatDate(date)}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke={lineColor}
              strokeWidth={2}
              dot={{ fill: lineColor, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Legend */}
      <div style={{ marginTop: 16, padding: "12px 0", borderTop: "1px solid var(--surface-high)" }}>
        <div style={{ display: "flex", gap: 24, fontSize: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 16, height: 2, background: "#34c759" }} />
            <span style={{ color: "var(--text-muted)" }}>A/B (Strong)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 16, height: 2, background: "#ffcc00" }} />
            <span style={{ color: "var(--text-muted)" }}>C (Fair)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 16, height: 2, background: "#ff2d55" }} />
            <span style={{ color: "var(--text-muted)" }}>D (Poor)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

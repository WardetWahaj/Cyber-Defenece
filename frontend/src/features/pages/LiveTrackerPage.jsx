import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { api } from "../../lib/api";

export default function LiveTrackerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [target, setTarget] = useState("example.com");
  const [jobId, setJobId] = useState("");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    const qJob = searchParams.get("jobId") || "";
    const qTarget = searchParams.get("target") || "";
    if (qTarget) setTarget(qTarget);
    if (qJob) setJobId(qJob);
  }, [searchParams]);

  useEffect(() => {
    if (!jobId) return undefined;
    const interval = setInterval(async () => {
      try {
        const state = await api.liveStatus(jobId);
        setJob(state);
        if (["completed", "cancelled"].includes(state.status)) {
          clearInterval(interval);
        }
      } catch (e) {
        setError(String(e.message || e));
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  const progress = job?.overall_progress ?? 0;
  const kpis = job?.kpis || {
    threats_neutralized: 0,
    open_ports_found: 0,
    throughput: "0.0 GB/s",
  };

  const statusColor = useMemo(() => {
    if (job?.status === "completed") return "#45dfa4";
    if (job?.status === "cancelled") return "#ffb4ab";
    return "#fbbf24";
  }, [job?.status]);

  async function startScan() {
    setStarting(true);
    setError("");
    try {
      const started = await api.liveStart(target);
      setJobId(started.job_id);
      setSearchParams({ jobId: started.job_id, target });
      const state = await api.liveStatus(started.job_id);
      setJob(state);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setStarting(false);
    }
  }

  async function cancelScan() {
    if (!jobId) return;
    try {
      await api.liveCancel(jobId);
      const state = await api.liveStatus(jobId);
      setJob(state);
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  return (
    <>
      <PageTitle title="Live Scan Progress Tracker" subtitle="Real-time polling with module timeline, subsystem progress, and console telemetry." />

      <Card title="SCAN IN PROGRESS" right={<strong style={{ color: statusColor }}>{(job?.status || "idle").toUpperCase()}</strong>}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="example.com"
            style={{ flex: 1, background: "var(--surface-high)", border: "1px solid var(--ghost)", color: "var(--text)", padding: 10, borderRadius: 6 }}
          />
          <Button onClick={startScan} disabled={starting || !target}>{starting ? "Starting..." : "Start Live Scan"}</Button>
          <Button variant="secondary" onClick={cancelScan} disabled={!jobId}>Cancel</Button>
        </div>
        {jobId && <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>SESSION ID: {jobId}</div>}
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

      <div className="grid grid-4" style={{ marginTop: 16 }}>
        <Card title="OVERALL PROGRESS">
          <div className="kpi-value">{progress.toFixed(1)}%</div>
          <div style={{ background: "var(--surface-high)", height: 8, borderRadius: 999, overflow: "hidden", marginTop: 8 }}>
            <div style={{ width: `${progress}%`, height: "100%", background: "linear-gradient(135deg, #3B82F6, #2563eb)" }} />
          </div>
          <p style={{ marginTop: 8, fontSize: 12, color: "var(--text-secondary)" }}>TIME REMAINING: {job?.time_remaining || "~4:38"}</p>
        </Card>
        <Card title="THREATS NEUTRALIZED"><div className="kpi-value" style={{ color: "#45dfa4" }}>{kpis.threats_neutralized}</div></Card>
        <Card title="OPEN PORTS FOUND"><div className="kpi-value">{kpis.open_ports_found}</div></Card>
        <Card title="THROUGHPUT"><div className="kpi-value">{kpis.throughput}</div></Card>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16 }}>
        <Card title="MODULE PROGRESS TIMELINE">
          {(job?.modules || []).map((m) => (
            <div key={m.id} style={{ marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--ghost)" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>MODULE {String(m.id).padStart(2, "0")}: {m.name}</strong>
                <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{m.elapsed}</span>
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>{m.status.toUpperCase()} ({m.progress}%)</div>
              <div style={{ background: "var(--surface-high)", height: 6, borderRadius: 999, overflow: "hidden", marginTop: 6 }}>
                <div style={{ width: `${m.progress}%`, height: "100%", background: m.status === "completed" ? "#45dfa4" : "#3B82F6" }} />
              </div>
            </div>
          ))}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={{ background: "var(--surface-high)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 10 }}>
              <div style={{ fontSize: 11, color: "var(--text-secondary)", textTransform: "uppercase" }}>SQL Injection Probe</div>
              <div style={{ fontWeight: 700 }}>{job?.subtasks?.sql_injection_probe?.status || "queued"}</div>
            </div>
            <div style={{ background: "var(--surface-high)", border: "1px solid var(--ghost)", borderRadius: 6, padding: 10 }}>
              <div style={{ fontSize: 11, color: "var(--text-secondary)", textTransform: "uppercase" }}>Buffer Overflow Tests</div>
              <div style={{ fontWeight: 700 }}>{job?.subtasks?.buffer_overflow_tests?.status || "queued"}</div>
            </div>
          </div>
        </Card>

        <Card title="SYSTEM CONSOLE [v1.2]">
          <div style={{ maxHeight: 320, overflow: "auto", background: "#060d20", borderRadius: 6, padding: 10, border: "1px solid var(--ghost)" }}>
            {(job?.console || []).map((line, index) => (
              <div key={`${line}-${index}`} style={{ fontFamily: "monospace", fontSize: 12, color: "#8d90a0", marginBottom: 6 }}>
                {line}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  );
}

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    target: "",
    scan_mode: "Comprehensive",
    frequency: "weekly",
  });

  // Fetch schedules on mount
  useEffect(() => {
    fetchSchedules();
  }, []);

  async function fetchSchedules() {
    try {
      setLoading(true);
      setError("");
      const data = await api.getSchedules();
      setSchedules(data.schedules || []);
    } catch (err) {
      setError(err.message);
      console.error("Failed to fetch schedules:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateSchedule() {
    if (!formData.target.trim()) {
      setError("Target cannot be empty");
      return;
    }

    try {
      setError("");
      await api.createSchedule({
        target: formData.target,
        scan_mode: formData.scan_mode,
        frequency: formData.frequency,
      });
      setFormData({ target: "", scan_mode: "Comprehensive", frequency: "weekly" });
      setShowForm(false);
      await fetchSchedules();
    } catch (err) {
      setError(err.message);
      console.error("Failed to create schedule:", err);
    }
  }

  async function handleDeleteSchedule(scheduleId) {
    if (!confirm("Are you sure you want to delete this schedule?")) return;

    try {
      setError("");
      await api.deleteSchedule(scheduleId);
      await fetchSchedules();
    } catch (err) {
      setError(err.message);
      console.error("Failed to delete schedule:", err);
    }
  }

  async function handleToggleSchedule(scheduleId) {
    try {
      setError("");
      await api.toggleSchedule(scheduleId);
      await fetchSchedules();
    } catch (err) {
      setError(err.message);
      console.error("Failed to toggle schedule:", err);
    }
  }

  function formatDate(dateString) {
    if (!dateString) return "—";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  }

  return (
    <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ marginBottom: "8px", fontSize: "28px", fontWeight: 700 }}>Scheduled Scans</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "24px", fontSize: 13 }}>
        Scheduled scans will run automatically via Heroku Scheduler. Configure your recurring security scans below.
      </p>

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

      {/* New Schedule Button */}
      <button
        onClick={() => setShowForm(!showForm)}
        style={{
          padding: "10px 16px",
          borderRadius: 6,
          border: "1px solid var(--primary)",
          background: "var(--primary)",
          color: "white",
          cursor: "pointer",
          fontSize: 13,
          fontWeight: 600,
          marginBottom: "20px",
        }}
      >
        {showForm ? "Cancel" : "+ New Schedule"}
      </button>

      {/* Create Schedule Form */}
      {showForm && (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--surface-high)",
            borderRadius: 8,
            padding: "16px",
            marginBottom: "24px",
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 14, fontWeight: 600 }}>Create New Schedule</h3>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Target</label>
              <input
                type="text"
                placeholder="example.com or IP address"
                value={formData.target}
                onChange={(e) => setFormData({ ...formData, target: e.target.value })}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: 6,
                  border: "1px solid var(--surface-high)",
                  background: "var(--surface-low)",
                  color: "var(--text)",
                  fontSize: 13,
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Scan Mode</label>
              <select
                value={formData.scan_mode}
                onChange={(e) => setFormData({ ...formData, scan_mode: e.target.value })}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: 6,
                  border: "1px solid var(--surface-high)",
                  background: "var(--surface-low)",
                  color: "var(--text)",
                  fontSize: 13,
                  boxSizing: "border-box",
                }}
              >
                <option>Comprehensive</option>
                <option>Quick</option>
                <option>Advanced</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Frequency</label>
              <select
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: 6,
                  border: "1px solid var(--surface-high)",
                  background: "var(--surface-low)",
                  color: "var(--text)",
                  fontSize: 13,
                  boxSizing: "border-box",
                }}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleCreateSchedule}
            style={{
              marginTop: 16,
              padding: "10px 16px",
              borderRadius: 6,
              border: "none",
              background: "var(--primary)",
              color: "white",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Create Schedule
          </button>
        </div>
      )}

      {/* Schedules Table */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
          Loading schedules...
        </div>
      ) : schedules.length === 0 ? (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--surface-high)",
            borderRadius: 8,
            padding: "40px",
            textAlign: "center",
            color: "var(--text-muted)",
          }}
        >
          <p style={{ margin: 0, fontSize: 14 }}>No scheduled scans yet. Create one to get started.</p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              background: "var(--surface)",
              borderRadius: 8,
              overflow: "hidden",
              border: "1px solid var(--surface-high)",
            }}
          >
            <thead>
              <tr style={{ borderBottom: "1px solid var(--surface-high)" }}>
                <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Target</th>
                <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Mode</th>
                <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Frequency</th>
                <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Next Run</th>
                <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Last Run</th>
                <th style={{ padding: "12px", textAlign: "center", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Status</th>
                <th style={{ padding: "12px", textAlign: "center", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((schedule, idx) => (
                <tr
                  key={schedule.id}
                  style={{
                    borderBottom: idx < schedules.length - 1 ? "1px solid var(--surface-high)" : "none",
                  }}
                >
                  <td style={{ padding: "12px", fontSize: 13 }}>{schedule.target}</td>
                  <td style={{ padding: "12px", fontSize: 13 }}>{schedule.scan_mode}</td>
                  <td style={{ padding: "12px", fontSize: 13, textTransform: "capitalize" }}>{schedule.frequency}</td>
                  <td style={{ padding: "12px", fontSize: 12, color: "var(--text-muted)" }}>{formatDate(schedule.next_run)}</td>
                  <td style={{ padding: "12px", fontSize: 12, color: "var(--text-muted)" }}>{formatDate(schedule.last_run)}</td>
                  <td style={{ padding: "12px", textAlign: "center" }}>
                    <div
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "4px 8px",
                        borderRadius: 4,
                        background: schedule.is_active ? "rgba(88, 166, 255, 0.1)" : "rgba(139, 148, 158, 0.1)",
                      }}
                    >
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: schedule.is_active ? "var(--primary)" : "var(--text-muted)",
                        }}
                      />
                      <span style={{ fontSize: 11, color: schedule.is_active ? "var(--primary)" : "var(--text-muted)", fontWeight: 600 }}>
                        {schedule.is_active ? "Active" : "Disabled"}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: "12px", textAlign: "center" }}>
                    <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
                      <button
                        onClick={() => handleToggleSchedule(schedule.id)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: 4,
                          border: "1px solid var(--surface-high)",
                          background: "var(--surface-low)",
                          color: "var(--text)",
                          cursor: "pointer",
                          fontSize: 11,
                          fontWeight: 600,
                        }}
                      >
                        {schedule.is_active ? "Disable" : "Enable"}
                      </button>
                      <button
                        onClick={() => handleDeleteSchedule(schedule.id)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: 4,
                          border: "1px solid #ffb4ab",
                          background: "rgba(255, 180, 171, 0.1)",
                          color: "#ffb4ab",
                          cursor: "pointer",
                          fontSize: 11,
                          fontWeight: 600,
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

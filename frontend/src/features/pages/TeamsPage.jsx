import { useEffect, useState } from "react";
import PageTitle from "../../components/ui/PageTitle";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { api } from "../../lib/api";

export default function TeamsPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");
  const [creating, setCreating] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [teamMembers, setTeamMembers] = useState([]);
  const [teamScans, setTeamScans] = useState([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const [inviting, setInviting] = useState(false);
  const [loadingTeamDetails, setLoadingTeamDetails] = useState(false);

  // Load teams on mount
  useEffect(() => {
    loadTeams();
  }, []);

  async function loadTeams() {
    try {
      setLoading(true);
      setError("");
      const data = await api.listTeams();
      setTeams(data || []);
    } catch (err) {
      setError(err.message);
      console.error("Failed to load teams:", err);
    } finally {
      setLoading(false);
    }
  }

  async function createTeam() {
    if (!newTeamName.trim()) {
      setError("Team name cannot be empty");
      return;
    }

    try {
      setCreating(true);
      setError("");
      await api.createTeam({ name: newTeamName });
      setNewTeamName("");
      setShowCreateModal(false);
      await loadTeams();
    } catch (err) {
      setError(err.message);
      console.error("Failed to create team:", err);
    } finally {
      setCreating(false);
    }
  }

  async function selectTeam(team) {
    try {
      setSelectedTeam(team);
      setLoadingTeamDetails(true);
      setError("");
      
      const [members, scans] = await Promise.all([
        api.getTeamMembers(team.id),
        api.getTeamScans(team.id),
      ]);
      
      setTeamMembers(members || []);
      setTeamScans(scans || []);
    } catch (err) {
      setError(err.message);
      console.error("Failed to load team details:", err);
    } finally {
      setLoadingTeamDetails(false);
    }
  }

  async function inviteUser() {
    if (!inviteEmail.trim()) {
      setError("Email cannot be empty");
      return;
    }

    try {
      setInviting(true);
      setError("");
      await api.inviteTeamMember(selectedTeam.id, {
        email: inviteEmail,
        role: inviteRole,
      });
      setInviteEmail("");
      setInviteRole("viewer");
      setShowInviteModal(false);
      await selectTeam(selectedTeam); // Refresh team details
    } catch (err) {
      setError(err.message);
      console.error("Failed to invite user:", err);
    } finally {
      setInviting(false);
    }
  }

  async function removeMember(userId) {
    if (!confirm("Remove this member from the team?")) return;

    try {
      setError("");
      await api.removeTeamMember(selectedTeam.id, userId);
      await selectTeam(selectedTeam); // Refresh team details
    } catch (err) {
      setError(err.message);
      console.error("Failed to remove member:", err);
    }
  }

  function getRoleBadgeColor(role) {
    switch (role) {
      case "owner":
        return { bg: "rgba(255, 193, 7, 0.12)", text: "#ffc107", label: "OWNER" };
      case "analyst":
        return { bg: "rgba(59, 130, 246, 0.12)", text: "var(--primary)", label: "ANALYST" };
      case "viewer":
        return { bg: "rgba(107, 114, 128, 0.12)", text: "#6b7280", label: "VIEWER" };
      default:
        return { bg: "rgba(107, 114, 128, 0.12)", text: "#6b7280", label: role.toUpperCase() };
    }
  }

  if (selectedTeam) {
    const currentUserRole = selectedTeam.role;
    const canInvite = currentUserRole === "owner" || currentUserRole === "analyst";
    const canRemove = currentUserRole === "owner";

    return (
      <>
        <PageTitle
          title={selectedTeam.name}
          subtitle={`${selectedTeam.member_count} members • ${selectedTeam.scan_count} shared scans`}
        />

        <button
          onClick={() => setSelectedTeam(null)}
          style={{
            padding: "8px 16px",
            borderRadius: 6,
            border: "1px solid var(--surface-high)",
            background: "var(--surface)",
            color: "var(--text)",
            cursor: "pointer",
            fontSize: 12,
            fontWeight: 600,
            marginBottom: 20,
          }}
        >
          ← Back to Teams
        </button>

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
            <p style={{ color: "#ffb4ab", fontSize: 13, margin: 0 }}>{error}</p>
            <button
              onClick={() => setError("")}
              style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid var(--surface-high)", background: "var(--surface)", color: "var(--primary)", cursor: "pointer", fontSize: 12 }}
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-2 page-section" style={{ gap: 16 }}>
          {/* Members Card */}
          <Card title="Team Members" right={canInvite ? <button className="btn btn-secondary" onClick={() => setShowInviteModal(true)}>+ Invite</button> : undefined}>
            {loadingTeamDetails ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 12, borderBottom: "1px solid rgba(67,70,85,0.15)" }}>
                    <Skeleton width={40} height={40} style={{ borderRadius: "50%" }} />
                    <div style={{ flex: 1 }}>
                      <Skeleton height={16} width="70%" />
                      <Skeleton height={12} width="50%" style={{ marginTop: 6 }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : teamMembers.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 12, margin: 0 }}>No members yet</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {teamMembers.map((member) => {
                  const roleBadge = getRoleBadgeColor(member.role);
                  return (
                    <div key={member.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: 12, borderBottom: "1px solid rgba(67,70,85,0.15)" }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: "var(--text)" }}>{member.full_name}</div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{member.email}</div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <Badge variant="secondary" style={{ background: roleBadge.bg, color: roleBadge.text }}>
                          {roleBadge.label}
                        </Badge>
                        {canRemove && member.role !== "owner" && (
                          <button
                            onClick={() => removeMember(member.user_id)}
                            style={{
                              padding: "4px 8px",
                              borderRadius: 4,
                              border: "1px solid #ff6b6b",
                              background: "transparent",
                              color: "#ff6b6b",
                              cursor: "pointer",
                              fontSize: 11,
                              fontWeight: 600,
                            }}
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Shared Scans Card */}
          <Card title="Shared Scans">
            {loadingTeamDetails ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} height={40} />
                ))}
              </div>
            ) : teamScans.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 12, margin: 0 }}>No scans shared yet</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {teamScans.map((scan) => (
                  <div key={scan.scan_id} style={{ background: "var(--surface-high)", borderRadius: 6, padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--text)" }}>Scan #{scan.scan_id}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        Shared by {scan.shared_by_name}
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {new Date(scan.shared_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Invite Modal */}
        {showInviteModal && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}>
            <div style={{
              background: "var(--surface)",
              border: "1px solid var(--surface-high)",
              borderRadius: 12,
              padding: 24,
              minWidth: 400,
              maxWidth: 500,
            }}>
              <h2 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 700 }}>Invite to {selectedTeam.name}</h2>

              {error && (
                <div style={{ background: "rgba(255, 107, 107, 0.1)", border: "1px solid #ffb4ab", borderRadius: 6, padding: 12, marginBottom: 16, color: "#ffb4ab", fontSize: 12 }}>
                  {error}
                </div>
              )}

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--text-muted)" }}>Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="user@example.com"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: 6,
                    border: "1px solid var(--surface-high)",
                    background: "var(--surface-low)",
                    color: "var(--text)",
                    fontSize: 13,
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: 20 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--text-muted)" }}>Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: 6,
                    border: "1px solid var(--surface-high)",
                    background: "var(--surface-low)",
                    color: "var(--text)",
                    fontSize: 13,
                  }}
                >
                  <option value="viewer">Viewer - View only</option>
                  <option value="analyst">Analyst - Run scans & reports</option>
                </select>
              </div>

              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                <button
                  onClick={() => setShowInviteModal(false)}
                  disabled={inviting}
                  style={{
                    padding: "10px 20px",
                    borderRadius: 6,
                    border: "1px solid var(--surface-high)",
                    background: "transparent",
                    color: "var(--text)",
                    cursor: "pointer",
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={inviteUser}
                  disabled={inviting}
                  style={{
                    padding: "10px 20px",
                    borderRadius: 6,
                    border: "none",
                    background: "var(--primary)",
                    color: "white",
                    cursor: "pointer",
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  {inviting ? "Inviting..." : "Send Invite"}
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <>
      <PageTitle
        title="Teams"
        subtitle="Collaborate with team members to manage security scans"
      />

      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <p style={{ color: "#ffb4ab", fontSize: 13, margin: 0 }}>{error}</p>
          <button
            onClick={() => { setError(""); loadTeams(); }}
            style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid var(--surface-high)", background: "var(--surface)", color: "var(--primary)", cursor: "pointer", fontSize: 12, whiteSpace: "nowrap" }}
          >
            Retry
          </button>
        </div>
      )}

      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          + Create Team
        </button>
      </div>

      {/* Create Team Modal */}
      {showCreateModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0, 0, 0, 0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--surface-high)",
            borderRadius: 12,
            padding: 24,
            minWidth: 400,
            maxWidth: 500,
          }}>
            <h2 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 700 }}>Create New Team</h2>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--text-muted)" }}>Team Name</label>
              <input
                type="text"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                placeholder="e.g., Security Team A"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  borderRadius: 6,
                  border: "1px solid var(--surface-high)",
                  background: "var(--surface-low)",
                  color: "var(--text)",
                  fontSize: 13,
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={creating}
                style={{
                  padding: "10px 20px",
                  borderRadius: 6,
                  border: "1px solid var(--surface-high)",
                  background: "transparent",
                  color: "var(--text)",
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Cancel
              </button>
              <button
                onClick={createTeam}
                disabled={creating}
                style={{
                  padding: "10px 20px",
                  borderRadius: 6,
                  border: "none",
                  background: "var(--primary)",
                  color: "white",
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {creating ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Teams Grid */}
      <div className="page-section">
        {loading ? (
          <div className="grid grid-3" style={{ gap: 16 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} title={<Skeleton width="80%" height={16} />}>
                <Skeleton height={16} width="60%" style={{ marginBottom: 8 }} />
                <Skeleton height={14} width="70%" />
              </Card>
            ))}
          </div>
        ) : teams.length === 0 ? (
          <Card title="No Teams Yet">
            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
              Create a team to start collaborating with your security team.
            </p>
          </Card>
        ) : (
          <div className="grid grid-3" style={{ gap: 16 }}>
            {teams.map((team) => {
              const roleBadge = getRoleBadgeColor(team.role);
              return (
                <div
                  key={team.id}
                  onClick={() => selectTeam(team)}
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--surface-high)",
                    borderRadius: 12,
                    padding: 16,
                    cursor: "pointer",
                    transition: "all 0.2s",
                    display: "flex",
                    flexDirection: "column",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--primary)";
                    e.currentTarget.style.background = "rgba(59, 130, 246, 0.05)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--surface-high)";
                    e.currentTarget.style.background = "var(--surface)";
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                    <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: "var(--text)" }}>{team.name}</h3>
                    <Badge variant="secondary" style={{ background: roleBadge.bg, color: roleBadge.text, whiteSpace: "nowrap" }}>
                      {roleBadge.label}
                    </Badge>
                  </div>

                  <div style={{ display: "flex", gap: 12, fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
                    <div>👥 {team.member_count} member{team.member_count !== 1 ? "s" : ""}</div>
                    <div>📊 {team.scan_count} scan{team.scan_count !== 1 ? "s" : ""}</div>
                  </div>

                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: "auto" }}>
                    Created {new Date(team.created_at).toLocaleDateString()}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}

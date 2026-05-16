import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const nav = [
  ["/", "Dashboard"],
  ["/scan/new", "New Scan"],
  ["/scan/live", "Live Tracker"],
  ["/results/vulnerabilities", "Vulnerabilities"],
  ["/results/defence", "Defence"],
  ["/results/virustotal", "VirusTotal"],
  ["/results/shodan", "Shodan Intel"],
  ["/results/abuseipdb", "AbuseIPDB"],
  ["/results/siem", "SIEM"],
  ["/reports/pdf", "PDF Generator"],
  ["/reports/history", "Reports History"],
  ["/schedules", "Schedules"],
  ["/settings", "Settings"],
];

export default function Sidebar({ mobileMenuOpen = false, onCloseMobileMenu = () => {} }) {
  const { user, logout } = useAuth();
  
  // Add admin link if user is admin
  const navItems = user?.role === "admin" ? [...nav, ["/admin", "Admin Panel"]] : nav;

  return (
    <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`} role="navigation" aria-label="Main navigation">
      <div style={{ marginBottom: 24 }}>
        <div className="sidebar-brand">CYBER DEFENCE</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 18 }}>
          <div style={{ width: 4, height: 32, borderRadius: 999, background: "linear-gradient(180deg, #3B82F6, #2563eb)" }} />
          <div>
            <div style={{ color: "var(--text)", fontSize: 12, fontWeight: 700, letterSpacing: "0.08em" }}>COMMAND CENTER</div>
            <div className="sidebar-section-label" style={{ marginTop: 2 }}>Active Session: Alpha-7</div>
          </div>
        </div>
      </div>

      <nav style={{ display: "grid", gap: 4 }}>
        {navItems.map(([to, label]) => {
          // We'll use a render function to access isActive state
          return (
            <NavLink
              key={to}
              to={to}
              onClick={onCloseMobileMenu}
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
            >
              {({ isActive }) => (
                <span {...(isActive ? { "aria-current": "page" } : {})}>
                  {label}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div style={{ marginTop: 24, display: "grid", gap: 4 }}>
        <div className="sidebar-link">Documentation</div>
        <div className="sidebar-link" onClick={() => { logout(); }} style={{ cursor: "pointer" }}>Log Out</div>
      </div>
    </aside>
  );
}

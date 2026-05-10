import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const nav = [
  ["/", "Dashboard"],
  ["/scan/new", "New Scan"],
  ["/scan/live", "Live Tracker"],
  ["/results/vulnerabilities", "Vulnerabilities"],
  ["/results/defence", "Defence"],
  ["/results/virustotal", "VirusTotal"],
  ["/results/siem", "SIEM"],
  ["/reports/pdf", "PDF Generator"],
  ["/reports/history", "Reports History"],
  ["/settings", "Settings"],
];

export default function Sidebar({ mobileMenuOpen = false, onCloseMobileMenu = () => {} }) {
  const { user } = useAuth();
  
  // Debug: Log user role for troubleshooting
  console.log('User role:', user?.role);
  
  // Add admin link if user is admin
  const navItems = user?.role === "admin" ? [...nav, ["/admin", "Admin Panel"]] : nav;

  return (
    <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
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
        {navItems.map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            onClick={onCloseMobileMenu}
            className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <div style={{ marginTop: 24, display: "grid", gap: 4 }}>
        <div className="sidebar-link">Documentation</div>
        <div className="sidebar-link">Log Out</div>
      </div>
    </aside>
  );
}

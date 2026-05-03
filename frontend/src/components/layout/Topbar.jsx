import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import "./Topbar.css";

export default function Topbar({ onOpenMobileMenu = () => {} }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [compactMode, setCompactMode] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem("darkMode");
    return saved ? JSON.parse(saved) : true; // Default to dark mode
  });

  useEffect(() => {
    // Apply theme changes
    localStorage.setItem("darkMode", JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add("dark-mode");
      document.documentElement.classList.remove("light-mode");
    } else {
      document.documentElement.classList.add("light-mode");
      document.documentElement.classList.remove("dark-mode");
    }
  }, [darkMode]);

  function toggleCompactMode() {
    const next = !compactMode;
    setCompactMode(next);
    document.body.style.fontSize = next ? "15px" : "";
  }

  function toggleTheme() {
    setDarkMode((prev) => !prev);
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="topbar">
      <button className="mobile-menu-btn material-symbols-outlined" onClick={onOpenMobileMenu}>menu</button>
      <div style={{ display: "flex", alignItems: "center", gap: 18, minWidth: 0 }}>
        <div className="shell-title">CYBER DEFENCE</div>
        <div className="topbar-search">
          <span className="material-symbols-outlined" style={{ fontSize: 18, color: "var(--text-muted)" }}>search</span>
          <input placeholder="Global threat lookup..." />
        </div>
      </div>

      <div className="topbar-actions">
        <button className="topbar-icon material-symbols-outlined" onClick={() => setShowNotifications((v) => !v)}>notifications</button>
        <button className="topbar-icon material-symbols-outlined" onClick={toggleTheme} title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>{darkMode ? "dark_mode" : "light_mode"}</button>
        <button className="topbar-icon material-symbols-outlined" onClick={() => navigate("/settings")}>settings</button>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginLeft: 6, position: "relative" }}>
          <button 
            className="topbar-profile-btn"
            onClick={() => setShowProfile((v) => !v)}
            title={user?.full_name}
          >
            <img
              alt="Analyst Profile Avatar"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC682aNGP5wNwKJOLVMg3CNGgyzEpR1iyKuvG0Q-_BEqLF_jcSYIQxn2IkGDo1-qwzPBKyScuD-ogziLOX_tm8gPRQjdAJoZAG5YgSwnfi8QS6CiXL6BxyElugtrpaeqv4TqZQQv4DIxDLxchoTjVPHUD3p1ys2gKkZS6mZfgwRC_NJWzEI1M9azW78sDgaacwo0H_cLIw496WHFYnp6Db6x0ALzUyQcCzV0qHoGVaU7uXaHV1s7wIg9w52xMI5ExMAuPdFMO_OWM8S"
              style={{ width: 32, height: 32, borderRadius: 999, objectFit: "cover", border: "1px solid rgba(67,70,85,0.3)" }}
              data-alt="Close-up portrait of a tech analyst in a dark room with blue ambient screen glow reflecting on face"
            />
          </button>
          {showProfile && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-header">
                <p style={{ margin: 0, fontWeight: 600 }}>{user?.full_name}</p>
                <p style={{ margin: 0, fontSize: 12, color: "var(--text-secondary)" }}>{user?.email}</p>
                {user?.organization && (
                  <p style={{ margin: 0, fontSize: 12, color: "var(--text-muted)" }}>{user.organization}</p>
                )}
              </div>
              <hr style={{ margin: "8px 0", border: "none", borderTop: "1px solid rgba(67,70,85,0.15)" }} />
              <button 
                className="profile-dropdown-item"
                onClick={() => {
                  navigate("/settings");
                  setShowProfile(false);
                }}
              >
                <span className="material-symbols-outlined">person</span>
                <span>Profile Settings</span>
              </button>
              <button 
                className="profile-dropdown-item"
                onClick={() => {
                  navigate("/reports/history");
                  setShowProfile(false);
                }}
              >
                <span className="material-symbols-outlined">history</span>
                <span>Scan History</span>
              </button>
              <hr style={{ margin: "8px 0", border: "none", borderTop: "1px solid rgba(67,70,85,0.15)" }} />
              <button 
                className="profile-dropdown-item logout"
                onClick={handleLogout}
              >
                <span className="material-symbols-outlined">logout</span>
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
      {showNotifications && (
        <div style={{ position: "absolute", right: 24, top: 56, width: 320, background: "#131b2e", border: "1px solid rgba(67,70,85,0.15)", borderRadius: 8, padding: 12, zIndex: 25 }}>
          <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 8 }}>Notifications</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Latest scan completed and reports are ready for review.</div>
        </div>
      )}
    </header>
  );
}

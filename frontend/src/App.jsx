import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ErrorBoundary from "./components/ui/ErrorBoundary";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import DashboardPage from "./features/pages/DashboardPage";
import NewScanPage from "./features/pages/NewScanPage";
import LiveTrackerPage from "./features/pages/LiveTrackerPage";
import VulnerabilityPage from "./features/pages/VulnerabilityPage";
import DefencePage from "./features/pages/DefencePage";
import VirusTotalPage from "./features/pages/VirusTotalPage";
import SiemPage from "./features/pages/SiemPage";
import PdfReportPage from "./features/pages/PdfReportPage";
import ReportsHistoryPage from "./features/pages/ReportsHistoryPage";
import SettingsPage from "./features/pages/SettingsPage";
import AdminPage from "./features/pages/AdminPage";
import LoginPage from "./features/pages/LoginPage";
import SignupPage from "./features/pages/SignupPage";
import ForgotPasswordPage from "./features/pages/ForgotPasswordPage";
import ResetPasswordPage from "./features/pages/ResetPasswordPage";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  const { loading } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Initialize theme on mount
  useEffect(() => {
    const savedDarkMode = localStorage.getItem("darkMode");
    const isDarkMode = savedDarkMode ? JSON.parse(savedDarkMode) : true;
    
    if (isDarkMode) {
      document.documentElement.classList.add("dark-mode");
      document.documentElement.classList.remove("light-mode");
    } else {
      document.documentElement.classList.add("light-mode");
      document.documentElement.classList.remove("dark-mode");
    }
  }, []);

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />

      {/* Protected Routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <div className="app-shell">
                <Sidebar mobileMenuOpen={mobileMenuOpen} onCloseMobileMenu={() => setMobileMenuOpen(false)} />
                <div 
                  className={`sidebar-overlay ${mobileMenuOpen ? 'mobile-open' : ''}`}
                  onClick={() => setMobileMenuOpen(false)}
                />
                <div>
                  <Topbar onOpenMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)} />
                  <main className="main-content page-frame">
                    <Routes>
                      <Route path="/" element={<DashboardPage />} />
                      <Route path="/scan/new" element={<NewScanPage />} />
                      <Route path="/scan/live" element={<LiveTrackerPage />} />
                      <Route path="/results/vulnerabilities" element={<VulnerabilityPage />} />
                      <Route path="/results/defence" element={<DefencePage />} />
                      <Route path="/results/virustotal" element={<VirusTotalPage />} />
                      <Route path="/results/siem" element={<SiemPage />} />
                      <Route path="/reports/pdf" element={<PdfReportPage />} />
                      <Route path="/reports/history" element={<ReportsHistoryPage />} />
                      <Route path="/settings" element={<SettingsPage />} />
                      <Route path="/admin" element={<AdminPage />} />
                    </Routes>
                  </main>
                </div>
              </div>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

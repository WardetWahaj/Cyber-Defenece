import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./AuthPages.css";

/**
 * ResetPasswordPage.jsx
 * 
 * Handles password reset using a token from the URL.
 * User gets redirected here after clicking the email link:
 * /reset-password/:token
 * 
 * Token is extracted from URL and sent with new password to backend.
 */
export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const { token } = useParams(); // Extract token from URL: /reset-password/TOKEN
  
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Handle password reset form submission
   * Validates passwords match, calls backend, clears token after success
   */
  async function handleResetPassword(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Client-side validation: passwords must match
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Client-side validation: minimum length
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    // Client-side validation: maximum byte length (Argon2id can handle longer, but UI enforces consistency)
    if (new TextEncoder().encode(newPassword).length > 72) {
      setError("Password is too long (maximum 72 bytes)");
      return;
    }

    setLoading(true);

    try {
      // Send reset request to backend with token and new password
      const response = await fetch("http://127.0.0.1:8000/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: token,           // Raw token from URL (backend will hash it to verify)
          new_password: newPassword
        })
      });

      if (!response.ok) {
        const data = await response.json();
        // Backend error - token invalid/expired or password validation failed
        throw new Error(data.detail || "Password reset failed");
      }

      const data = await response.json();
      
      // Success! Token is now invalidated in database, password is updated
      setSuccess("✅ Password reset successfully! Redirecting to login...");
      
      // Redirect to login page after 2 seconds
      setTimeout(() => {
        navigate("/login");
      }, 2000);
      
    } catch (err) {
      // Display error message
      setError(err.message || "Password reset failed");
    } finally {
      setLoading(false);
    }
  }

  // If no token in URL, this page shouldn't be accessed
  if (!token) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1>CyberDefence</h1>
            <p>Security Analysis Platform</p>
          </div>
          <div className="auth-form">
            <h2>Invalid Reset Link</h2>
            <div className="auth-error">No reset token provided. Please click the link in your email.</div>
            <div className="auth-links">
              <a href="/forgot-password">Request new reset link</a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>CyberDefence</h1>
          <p>Security Analysis Platform</p>
        </div>

        <form onSubmit={handleResetPassword} className="auth-form">
          <h2>Create New Password</h2>

          {/* Error messages */}
          {error && <div className="auth-error">{error}</div>}
          
          {/* Success messages */}
          {success && <div className="auth-success">{success}</div>}

          {/* New Password Input */}
          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={loading}
            />
            <small>At least 8 characters</small>
          </div>

          {/* Confirm Password Input */}
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={loading}
            />
          </div>

          {/* Submit Button */}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Resetting Password..." : "Reset Password"}
          </button>

          {/* Links */}
          <div className="auth-links">
            <a href="/login">Back to Login</a>
          </div>
        </form>
      </div>
    </div>
  );
}

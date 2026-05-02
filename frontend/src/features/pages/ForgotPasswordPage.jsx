import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./AuthPages.css";

/**
 * ForgotPasswordPage.jsx
 * 
 * Step 1 of Password Reset: Email Entry
 * User enters their email and receives a reset link via Gmail inbox.
 * 
 * ✅ PRODUCTION MODE: Reset link is sent via real Gmail SMTP
 * ✅ Security: Generic message returned (no email enumeration)
 */
export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState("email"); // "email" or "check-email"
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Handle email submission
   * Sends forgot-password request to backend which:
   * 1. Checks if user exists (but doesn't reveal it)
   * 2. Generates SHA-256 hashed reset token
   * 3. Stores token + expiry in database
   * 4. Sends reset link via real Gmail SMTP
   */
  async function handleEmailSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to request password reset");
      }

      const data = await response.json();
      
      // Success! Move to verification step
      setSuccess(data.message);
      setStep("check-email");
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>CyberDefence</h1>
          <p>Security Analysis Platform</p>
        </div>

        {/* Step 1: Email Entry */}
        {step === "email" && (
          <form onSubmit={handleEmailSubmit} className="auth-form">
            <h2>Forgot Password?</h2>

            {error && <div className="auth-error">{error}</div>}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@company.com"
                required
                disabled={loading}
              />
              <small>Enter the email associated with your account</small>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Sending..." : "Send Reset Link"}
            </button>

            <div className="auth-links">
              <Link to="/login">Back to Login</Link>
            </div>
          </form>
        )}

        {/* Step 2: Check Email */}
        {step === "check-email" && (
          <div className="auth-form">
            <h2>Check Your Email</h2>

            {success && <div className="auth-success">{success}</div>}

            <p>
              If this email is registered with CyberDefence, you will receive a password reset link.
            </p>

            <div style={{
              background: "#1a1f2e",
              border: "1px solid #238636",
              borderRadius: "6px",
              padding: "15px",
              margin: "20px 0",
              fontSize: "14px"
            }}>
              <strong>📧 Email Sent:</strong>
              <p>Check your Gmail inbox for a password reset link from CyberDefence.</p>
            </div>

            <div style={{
              background: "#1a1f2e",
              border: "1px solid #238636",
              borderRadius: "6px",
              padding: "15px",
              margin: "20px 0",
              fontSize: "14px"
            }}>
              <strong>Security Details:</strong>
              <ul style={{ marginTop: "10px" }}>
                <li>🕐 Link expires in 1 hour</li>
                <li>🔐 Works only once (one-time use)</li>
                <li>✅ SHA-256 encrypted tokens</li>
                <li>📨 Sent securely via Gmail</li>
              </ul>
            </div>

            <button 
              onClick={() => {
                setStep("email");
                setEmail("");
                setSuccess("");
              }}
              className="btn-primary"
              style={{ marginTop: "20px" }}
            >
              Try Another Email
            </button>

            <div className="auth-links">
              <Link to="/login">Back to Login</Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

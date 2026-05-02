import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import "./AuthPages.css";

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    organization: "",
    password: "",
    confirmPassword: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (new TextEncoder().encode(formData.password).length > 72) {
      setError("Password is too long (maximum 72 bytes)");
      return;
    }

    setLoading(true);

    try {
      await signup({
        email: formData.email,
        full_name: formData.full_name,
        organization: formData.organization,
        password: formData.password
      });
      navigate("/");
    } catch (err) {
      setError(err.message || "Signup failed");
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

        <form onSubmit={handleSignup} className="auth-form">
          <h2>Create Account</h2>

          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="analyst@company.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="full_name">Full Name</label>
            <input
              id="full_name"
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="John Doe"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="organization">Organization</label>
            <input
              id="organization"
              type="text"
              name="organization"
              value={formData.organization}
              onChange={handleChange}
              placeholder="ACME Corp"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
            <small>8-72 characters</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creating Account..." : "Create Account"}
          </button>

          <div className="auth-links">
            <p>Already have an account? <a href="/login">Sign In</a></p>
          </div>
        </form>
      </div>
    </div>
  );
}

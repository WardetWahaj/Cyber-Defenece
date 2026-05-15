import { Component } from "react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: "40px",
          textAlign: "center",
          color: "var(--text-muted)"
        }}>
          <h2 style={{ color: "var(--critical)", marginBottom: 12 }}>Something went wrong</h2>
          <p>{this.state.error?.message || "An unexpected error occurred"}</p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            style={{
              marginTop: 16,
              padding: "8px 20px",
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer"
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;

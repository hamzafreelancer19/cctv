import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const features = [
  "Real-time detection, tracking & face intelligence",
  "Life-safety AI: fire, smoke, weapons & falls",
  "Enterprise ops: notifications, evidence & SIEM",
];

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="hero-brand">
          <span className="brand-mark">SV</span>
          <div>
            <strong>SentinelVision AI</strong>
            <small className="muted" style={{ display: "block" }}>Enterprise Security Platform</small>
          </div>
        </div>
        <div>
          <h2>See everything. Miss nothing. Respond instantly.</h2>
          <p>
            An AI-native command center for smart security &amp; activity monitoring across every
            site, camera and edge device.
          </p>
          <div className="hero-features">
            {features.map((f) => (
              <div className="hero-feature" key={f}>
                <span className="tick">✓</span>
                {f}
              </div>
            ))}
          </div>
        </div>
        <div className="hero-foot">© {new Date().getFullYear()} SentinelVision AI · v1.0</div>
      </div>

      <div className="login-form-wrap">
        <form className="login-card" onSubmit={handleSubmit}>
          <div>
            <h1>Welcome back</h1>
            <p className="muted">Sign in to your control center</p>
          </div>
          {error && <div className="error-banner">{error}</div>}
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

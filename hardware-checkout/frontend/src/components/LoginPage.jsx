import { useState } from "react";
import { login } from "../api.js";
import { CheckIcon, LogoIcon } from "./Icons.jsx";
import NewUserModal from "./NewUserModal.jsx";
import { Message } from "./ui.jsx";

export default function LoginPage({ onLogin }) {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setNotice("");
    if (!userId || !password) {
      setError("Enter your userId and password");
      return;
    }
    setLoading(true);
    try {
      const data = await login(userId, password);
      onLogin(data.userId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleCreated(newUserId) {
    setShowModal(false);
    setUserId(newUserId);
    setPassword("");
    setError("");
    setNotice("Account created. Sign in to continue.");
  }

  const brand = (
    <div className="brand">
      <span className="brand-mark">
        <LogoIcon size={17} />
      </span>
      Hardware Checkout
    </div>
  );

  return (
    <div className="auth">
      <aside className="auth-brand">
        {brand}
        <div className="auth-pitch">
          <h1>Track every hardware set across your team's projects.</h1>
          <p>Create projects, bring in teammates, and check hardware in and out against live availability.</p>
          <ul className="auth-points">
            <li>
              <CheckIcon size={14} />
              Live capacity and availability
            </li>
            <li>
              <CheckIcon size={14} />
              Shared projects with owner controls
            </li>
            <li>
              <CheckIcon size={14} />
              Per-project checkout totals
            </li>
          </ul>
        </div>
        <div className="auth-foot">Software Lab · Hardware Checkout System</div>
      </aside>

      <main className="auth-main">
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-mobile-brand">{brand}</div>
          <header>
            <h1>Sign in</h1>
            <p>Welcome back. Enter your details to continue.</p>
          </header>

          <label className="field">
            <span>User ID</span>
            <input
              className="input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              autoComplete="username"
              placeholder="Your user ID"
              autoFocus
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </label>

          <Message msg={error ? { type: "error", text: error } : notice ? { type: "notice", text: notice } : null} />

          <button type="submit" className="btn primary block" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <div className="divider">New here?</div>

          <button type="button" className="btn secondary block" onClick={() => setShowModal(true)}>
            Create an account
          </button>
        </form>
      </main>

      {showModal && <NewUserModal onClose={() => setShowModal(false)} onCreated={handleCreated} />}
    </div>
  );
}

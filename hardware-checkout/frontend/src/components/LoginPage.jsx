import { useState } from "react";
import { login } from "../api.js";
import NewUserModal from "./NewUserModal.jsx";

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

  return (
    <main className="page">
      <form className="card" onSubmit={handleSubmit}>
        <h1>Hardware Checkout</h1>
        <p className="subtitle">Sign in to manage your projects</p>

        <label>
          User ID
          <input value={userId} onChange={(e) => setUserId(e.target.value)} autoComplete="username" />
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

        {error && <p className="error">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <button type="button" className="secondary" onClick={() => setShowModal(true)}>
          New User
        </button>
      </form>

      {showModal && <NewUserModal onClose={() => setShowModal(false)} onCreated={handleCreated} />}
    </main>
  );
}

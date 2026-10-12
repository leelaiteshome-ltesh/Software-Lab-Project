import { useState } from "react";
import { signUp } from "../api.js";

export default function NewUserModal({ onClose, onCreated }) {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!userId || !password) {
      setError("Enter a userId and password");
      return;
    }
    if (/[ !]/.test(userId) || /[ !]/.test(password)) {
      setError("userId and password can't contain spaces or '!'");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    try {
      await signUp(userId, password);
      onCreated(userId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <form className="card modal" onSubmit={handleSubmit} onClick={(e) => e.stopPropagation()}>
        <h2>Create account</h2>

        <label>
          New user ID
          <input value={userId} onChange={(e) => setUserId(e.target.value)} autoFocus />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <label>
          Confirm password
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Creating..." : "Create account"}
        </button>
        <button type="button" className="secondary" onClick={onClose}>
          Cancel
        </button>
      </form>
    </div>
  );
}

import { useEffect, useState } from "react";
import { signUp } from "../api.js";
import { XIcon } from "./Icons.jsx";
import { Message } from "./ui.jsx";

export default function NewUserModal({ onClose, onCreated }) {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

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
      <form
        className="modal"
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-user-title"
      >
        <div className="modal-header">
          <div>
            <h2 id="new-user-title">Create your account</h2>
            <p>Pick a user ID and password to get started.</p>
          </div>
          <button type="button" className="btn ghost icon-only" onClick={onClose} aria-label="Close">
            <XIcon size={18} />
          </button>
        </div>

        <div className="modal-body">
          <label className="field">
            <span>User ID</span>
            <input className="input" value={userId} onChange={(e) => setUserId(e.target.value)} autoFocus />
            <small className="hint">No spaces or “!”.</small>
          </label>
          <label className="field">
            <span>Password</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />
          </label>
          <label className="field">
            <span>Confirm password</span>
            <input
              className="input"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
            />
          </label>

          <Message msg={error ? { type: "error", text: error } : null} />
        </div>

        <div className="modal-footer">
          <button type="button" className="btn secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={loading}>
            {loading ? "Creating…" : "Create account"}
          </button>
        </div>
      </form>
    </div>
  );
}

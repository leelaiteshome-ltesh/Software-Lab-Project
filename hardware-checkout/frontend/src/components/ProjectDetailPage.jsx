import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  checkIn,
  checkOut,
  deleteProject,
  getHardwareSets,
  getProject,
  getProjectHardware,
  leaveProject,
  removeMember,
} from "../api.js";

export default function ProjectDetailPage({ userId, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [sets, setSets] = useState([]);
  const [held, setHeld] = useState({}); // hwSetId -> quantity this project has out
  const [qty, setQty] = useState({}); // hwSetId -> text in the quantity box
  const [loadError, setLoadError] = useState("");
  const [hwMsg, setHwMsg] = useState({ type: "", text: "" });
  const [memberMsg, setMemberMsg] = useState({ type: "", text: "" });
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const [p, allSets, mine] = await Promise.all([
        getProject(userId, projectId),
        getHardwareSets(),
        getProjectHardware(userId, projectId),
      ]);
      setProject(p);
      setSets(allSets);
      setHeld(Object.fromEntries(mine.map((h) => [h.hwSetId, h.quantity])));
    } catch (err) {
      setLoadError(err.message);
    }
  }

  useEffect(() => {
    refresh();
  }, [userId, projectId]);

  const isOwner = project && project.owner === userId;

  async function handleHardware(action, hwSetId) {
    setHwMsg({ type: "", text: "" });
    const n = Number(qty[hwSetId]);
    if (!Number.isInteger(n) || n < 1) {
      setHwMsg({ type: "error", text: "Enter a whole number of at least 1" });
      return;
    }
    setBusy(true);
    try {
      const fn = action === "out" ? checkOut : checkIn;
      const res = await fn(userId, project.projectId, hwSetId, n);
      setHwMsg({ type: "notice", text: res.message });
      setQty({ ...qty, [hwSetId]: "" });
      await refresh();
    } catch (err) {
      setHwMsg({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(memberId) {
    if (!confirm(`Remove ${memberId} from this project?`)) return;
    setMemberMsg({ type: "", text: "" });
    try {
      setProject(await removeMember(userId, project.projectId, memberId));
      setMemberMsg({ type: "notice", text: `Removed ${memberId}` });
    } catch (err) {
      setMemberMsg({ type: "error", text: err.message });
    }
  }

  async function handleLeave() {
    if (!confirm("Leave this project?")) return;
    try {
      await leaveProject(userId, project.projectId);
      navigate("/projects");
    } catch (err) {
      setMemberMsg({ type: "error", text: err.message });
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${project.name}"? This can't be undone.`)) return;
    try {
      await deleteProject(userId, project.projectId);
      navigate("/projects");
    } catch (err) {
      setMemberMsg({ type: "error", text: err.message });
    }
  }

  return (
    <main className="page wide">
      <div className="topbar">
        <Link to="/projects">← Projects</Link>
        <span>
          Signed in as <b>{userId}</b>{" "}
          <button className="secondary small" onClick={onLogout}>
            Log out
          </button>
        </span>
      </div>

      {loadError ? (
        <div className="card">
          <p className="error">{loadError}</p>
        </div>
      ) : !project ? (
        <div className="card">
          <p className="subtitle">Loading...</p>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="row">
              <h1>{project.name}</h1>
              <code>{project.projectId}</code>
              <span className={`badge ${isOwner ? "owner" : "member"}`}>{isOwner ? "Owner" : "Member"}</span>
            </div>
            {project.description && <p className="subtitle">{project.description}</p>}
          </div>

          <div className="card">
            <h2>Hardware</h2>
            <table className="hw-table">
              <thead>
                <tr>
                  <th>Set</th>
                  <th>Available</th>
                  <th>This project</th>
                  <th>Quantity</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {sets.map((s) => (
                  <tr key={s.hwSetId}>
                    <td>
                      <b>{s.hwSetId}</b>
                      <div className="meta">{s.name}</div>
                    </td>
                    <td>
                      {s.availability} / {s.capacity}
                    </td>
                    <td>{held[s.hwSetId] || 0}</td>
                    <td>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        className="qty"
                        value={qty[s.hwSetId] || ""}
                        onChange={(e) => setQty({ ...qty, [s.hwSetId]: e.target.value })}
                      />
                    </td>
                    <td className="actions">
                      <button className="primary small" disabled={busy} onClick={() => handleHardware("out", s.hwSetId)}>
                        Check out
                      </button>
                      <button
                        className="secondary small"
                        disabled={busy || !held[s.hwSetId]}
                        onClick={() => handleHardware("in", s.hwSetId)}
                      >
                        Check in
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {hwMsg.text && <p className={hwMsg.type}>{hwMsg.text}</p>}
          </div>

          <div className="card list">
            <h2>Members</h2>
            <ul>
              {project.members.map((m) => (
                <li key={m} className="row">
                  <span>
                    {m}
                    {m === userId && " (you)"}
                  </span>
                  {m === project.owner ? (
                    <span className="badge owner">Owner</span>
                  ) : (
                    <span className="badge member">Member</span>
                  )}
                  {isOwner && m !== project.owner && (
                    <button className="secondary small push-right" onClick={() => handleRemove(m)}>
                      Remove
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {memberMsg.text && <p className={memberMsg.type}>{memberMsg.text}</p>}
            {isOwner ? (
              <button className="danger" onClick={handleDelete}>
                Delete project
              </button>
            ) : (
              <button className="secondary" onClick={handleLeave}>
                Leave project
              </button>
            )}
          </div>
        </>
      )}
    </main>
  );
}

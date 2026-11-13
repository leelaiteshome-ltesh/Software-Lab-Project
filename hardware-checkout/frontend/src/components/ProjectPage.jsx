import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  checkIn,
  checkOut,
  deleteProject,
  getProject,
  getProjectHardware,
  leaveProject,
  removeMember,
} from "../api.js";

export default function ProjectPage({ userId, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [hardware, setHardware] = useState([]);
  const [quantities, setQuantities] = useState({});
  const [loadError, setLoadError] = useState("");
  const empty = { type: "", text: "" };
  const [hwMsg, setHwMsg] = useState(empty);
  const [memberMsg, setMemberMsg] = useState(empty);
  const [manageMsg, setManageMsg] = useState(empty);
  const [busy, setBusy] = useState(false);

  const isOwner = project?.owner === userId;

  async function load() {
    try {
      const [p, hw] = await Promise.all([getProject(userId, projectId), getProjectHardware(userId, projectId)]);
      setProject(p);
      setHardware(hw);
    } catch (err) {
      setLoadError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [userId, projectId]);

  async function run(setMsg, action, success) {
    setHwMsg(empty);
    setMemberMsg(empty);
    setManageMsg(empty);
    setBusy(true);
    try {
      await action();
      if (success) setMsg({ type: "notice", text: success });
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  function handleHardware(hwSetId, direction) {
    const raw = (quantities[hwSetId] || "").trim();
    if (!/^\d+$/.test(raw) || Number(raw) < 1) {
      setHwMsg({ type: "error", text: "Quantity must be a whole number of at least 1" });
      return;
    }
    const qty = Number(raw);
    const fn = direction === "out" ? checkOut : checkIn;
    run(setHwMsg, async () => {
      setHardware(await fn(userId, projectId, hwSetId, qty));
      setQuantities((q) => ({ ...q, [hwSetId]: "" }));
    }, `${direction === "out" ? "Checked out" : "Checked in"} ${qty} unit(s) of ${hwSetId}`);
  }

  function handleRemove(memberId) {
    if (!window.confirm(`Remove ${memberId} from this project?`)) return;
    run(setMemberMsg, async () => setProject(await removeMember(userId, projectId, memberId)), `Removed ${memberId}`);
  }

  function handleDelete() {
    if (!window.confirm(`Delete project "${project.name}"? This can't be undone.`)) return;
    run(setManageMsg, async () => {
      await deleteProject(userId, projectId);
      navigate("/projects");
    });
  }

  function handleLeave() {
    if (!window.confirm(`Leave project "${project.name}"?`)) return;
    run(setManageMsg, async () => {
      await leaveProject(userId, projectId);
      navigate("/projects");
    });
  }

  const topbar = (
    <div className="topbar">
      <Link to="/projects">← Projects</Link>
      <span>
        Signed in as <b>{userId}</b>{" "}
        <button className="secondary small" onClick={onLogout}>
          Log out
        </button>
      </span>
    </div>
  );

  if (loadError) {
    return (
      <main className="page wide">
        {topbar}
        <div className="card">
          <p className="error">{loadError}</p>
        </div>
      </main>
    );
  }

  if (!project) {
    return (
      <main className="page wide">
        {topbar}
        <div className="card">
          <p className="subtitle">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="page wide">
      {topbar}

      <div className="card">
        <div className="title-row">
          <h1>{project.name}</h1>
          <span className={`badge ${isOwner ? "owner" : "member"}`}>{isOwner ? "Owner" : "Member"}</span>
        </div>
        <p className="subtitle">
          <code>{project.projectId}</code>
          {project.description && <> · {project.description}</>}
        </p>
      </div>

      <div className="card">
        <h2>Hardware</h2>
        <table className="hw-table">
          <thead>
            <tr>
              <th>Set</th>
              <th>Capacity</th>
              <th>Available</th>
              <th>This project</th>
              <th>Quantity</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {hardware.map((h) => (
              <tr key={h.hwSetId}>
                <td><b>{h.hwSetId}</b></td>
                <td>{h.capacity}</td>
                <td>{h.availability}</td>
                <td>{h.checkedOut}</td>
                <td>
                  <input
                    className="qty"
                    inputMode="numeric"
                    placeholder="0"
                    value={quantities[h.hwSetId] || ""}
                    onChange={(e) => setQuantities((q) => ({ ...q, [h.hwSetId]: e.target.value }))}
                  />
                </td>
                <td className="actions">
                  <button className="primary small" disabled={busy} onClick={() => handleHardware(h.hwSetId, "out")}>
                    Check out
                  </button>
                  <button className="secondary small" disabled={busy} onClick={() => handleHardware(h.hwSetId, "in")}>
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
            <li key={m} className="member-row">
              <span>
                {m} {m === project.owner && <span className="badge owner">Owner</span>}
                {m === userId && <span className="subtitle inline"> (you)</span>}
              </span>
              {isOwner && m !== project.owner && (
                <button className="secondary small" disabled={busy} onClick={() => handleRemove(m)}>
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>
        {memberMsg.text && <p className={memberMsg.type}>{memberMsg.text}</p>}
      </div>

      <div className="card">
        {isOwner ? (
          <>
            <h2>Delete project</h2>
            <p className="subtitle">All hardware must be checked in first.</p>
            <button className="danger" disabled={busy} onClick={handleDelete}>
              Delete project
            </button>
          </>
        ) : (
          <>
            <h2>Leave project</h2>
            <p className="subtitle">Hardware checked out to this project stays with it.</p>
            <button className="danger" disabled={busy} onClick={handleLeave}>
              Leave project
            </button>
          </>
        )}
        {manageMsg.text && <p className={manageMsg.type}>{manageMsg.text}</p>}
      </div>
    </main>
  );
}

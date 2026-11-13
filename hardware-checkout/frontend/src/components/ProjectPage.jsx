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
import AppShell from "./AppShell.jsx";
import { AlertIcon, ChevronLeftIcon, CpuIcon, LogOutIcon, TrashIcon, UsersIcon } from "./Icons.jsx";
import { Avatar, CopyChip, Empty, Message, Meter, RoleBadge, Skeleton, SkeletonRows } from "./ui.jsx";

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

  const back = (
    <Link to="/projects" className="back-link">
      <ChevronLeftIcon size={16} />
      All projects
    </Link>
  );

  if (loadError) {
    return (
      <AppShell userId={userId} onLogout={onLogout}>
        <div>{back}</div>
        <div className="card">
          <Empty
            icon={<AlertIcon size={22} />}
            title="Couldn't open this project"
            text={loadError}
            action={
              <Link to="/projects" className="btn secondary sm">
                Back to projects
              </Link>
            }
          />
        </div>
      </AppShell>
    );
  }

  if (!project) {
    return (
      <AppShell userId={userId} onLogout={onLogout}>
        <div className="skeleton-stack">
          {back}
          <Skeleton w={260} h={30} />
          <Skeleton w={200} h={14} />
        </div>
        <div className="card">
          <SkeletonRows count={3} />
        </div>
      </AppShell>
    );
  }

  const totalHeld = hardware.reduce((s, h) => s + h.checkedOut, 0);

  return (
    <AppShell userId={userId} onLogout={onLogout}>
      <div>
        {back}
        <div className="page-header">
          <div>
            <div className="title-row">
              <h1>{project.name}</h1>
              <RoleBadge owner={isOwner} />
            </div>
            <div className="project-meta">
              <CopyChip value={project.projectId} />
              <span className="dot">·</span>
              <span className="meta-item">
                <UsersIcon size={14} />
                {project.members.length} member{project.members.length === 1 ? "" : "s"}
              </span>
              <span className="dot">·</span>
              <span className="meta-item">
                <CpuIcon size={14} />
                {totalHeld} unit{totalHeld === 1 ? "" : "s"} checked out
              </span>
            </div>
            {project.description && <p className="project-desc">{project.description}</p>}
          </div>
        </div>
      </div>

      <section className="card">
        <div className="card-header">
          <div>
            <h2>Hardware</h2>
            <p>Check units out to this project or return them to the shelf.</p>
          </div>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Hardware set</th>
                <th>Availability</th>
                <th className="num">Held by project</th>
                <th className="num">Quantity</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {hardware.map((h) => (
                <tr key={h.hwSetId}>
                  <td>
                    <div className="hw-name">
                      <span className="hw-icon">
                        <CpuIcon size={16} />
                      </span>
                      {h.hwSetId}
                    </div>
                  </td>
                  <td>
                    <div className="avail-cell">
                      <Meter value={h.availability} max={h.capacity} />
                      <span className="meta">
                        {h.availability} of {h.capacity} available
                      </span>
                    </div>
                  </td>
                  <td className="num">
                    <span className={`held${h.checkedOut ? "" : " zero"}`}>{h.checkedOut}</span>
                  </td>
                  <td className="num">
                    <input
                      className="input sm"
                      inputMode="numeric"
                      placeholder="0"
                      aria-label={`Quantity for ${h.hwSetId}`}
                      value={quantities[h.hwSetId] || ""}
                      onChange={(e) => setQuantities((q) => ({ ...q, [h.hwSetId]: e.target.value }))}
                    />
                  </td>
                  <td>
                    <div className="actions">
                      <button className="btn primary sm" disabled={busy} onClick={() => handleHardware(h.hwSetId, "out")}>
                        Check out
                      </button>
                      <button className="btn secondary sm" disabled={busy} onClick={() => handleHardware(h.hwSetId, "in")}>
                        Check in
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {hwMsg.text && (
          <div className="card-msg">
            <Message msg={hwMsg} />
          </div>
        )}
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="card-header">
            <div>
              <h2>Members</h2>
              <p>Everyone with access to this project</p>
            </div>
          </div>
          <ul className="rows">
            {project.members.map((m) => (
              <li key={m} className="row">
                <Avatar name={m} size={34} />
                <div className="row-main">
                  <div className="row-title">
                    {m}
                    {m === userId && <span className="muted you">(you)</span>}
                  </div>
                  <div className="row-sub">{m === project.owner ? "Owner" : "Member"}</div>
                </div>
                {isOwner && m !== project.owner && (
                  <button className="btn ghost sm" disabled={busy} onClick={() => handleRemove(m)}>
                    Remove
                  </button>
                )}
              </li>
            ))}
          </ul>
          {memberMsg.text && (
            <div className="card-msg">
              <Message msg={memberMsg} />
            </div>
          )}
        </section>

        <section className="card danger-zone">
          <div className="card-header">
            <div>
              <h2>Danger zone</h2>
              <p>These actions can't be undone.</p>
            </div>
          </div>
          <div className="danger-row">
            {isOwner ? (
              <>
                <div>
                  <b>Delete this project</b>
                  <p>All hardware must be checked in first.</p>
                </div>
                <button className="btn danger-outline" disabled={busy} onClick={handleDelete}>
                  <TrashIcon size={16} />
                  Delete project
                </button>
              </>
            ) : (
              <>
                <div>
                  <b>Leave this project</b>
                  <p>Hardware checked out to this project stays with it.</p>
                </div>
                <button className="btn danger-outline" disabled={busy} onClick={handleLeave}>
                  <LogOutIcon size={16} />
                  Leave project
                </button>
              </>
            )}
          </div>
          {manageMsg.text && (
            <div className="card-msg">
              <Message msg={manageMsg} />
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

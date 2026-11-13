import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createProject, getMyProjects, joinProject } from "../api.js";
import AppShell from "./AppShell.jsx";
import { FolderIcon, LinkIcon, PlusIcon, UsersIcon } from "./Icons.jsx";
import { Empty, Message, RoleBadge, Skeleton } from "./ui.jsx";

export default function ProjectsPage({ userId, onLogout }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState("");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [newId, setNewId] = useState("");
  const [createMsg, setCreateMsg] = useState({ type: "", text: "" });
  const [creating, setCreating] = useState(false);

  const [existingId, setExistingId] = useState("");
  const [joinMsg, setJoinMsg] = useState({ type: "", text: "" });
  const [joining, setJoining] = useState(false);

  async function refresh() {
    try {
      setProjects(await getMyProjects(userId));
    } catch (err) {
      setListError(err.message);
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [userId]);

  async function handleCreate(e) {
    e.preventDefault();
    setCreateMsg({ type: "", text: "" });
    if (!name.trim() || !newId.trim()) {
      setCreateMsg({ type: "error", text: "Project name and ProjectID are required" });
      return;
    }
    setCreating(true);
    try {
      const p = await createProject(userId, newId, name, description);
      setCreateMsg({ type: "notice", text: `Created "${p.name}" (${p.projectId})` });
      setName("");
      setDescription("");
      setNewId("");
      navigate(`/projects/${encodeURIComponent(p.projectId)}`);
    } catch (err) {
      setCreateMsg({ type: "error", text: err.message });
    } finally {
      setCreating(false);
    }
  }

  async function handleJoin(e) {
    e.preventDefault();
    setJoinMsg({ type: "", text: "" });
    if (!existingId.trim()) {
      setJoinMsg({ type: "error", text: "Enter a ProjectID" });
      return;
    }
    setJoining(true);
    try {
      const p = await joinProject(userId, existingId);
      setJoinMsg({ type: "notice", text: `Joined "${p.name}"` });
      setExistingId("");
      navigate(`/projects/${encodeURIComponent(p.projectId)}`);
    } catch (err) {
      setJoinMsg({ type: "error", text: err.message });
    } finally {
      setJoining(false);
    }
  }

  return (
    <AppShell userId={userId} onLogout={onLogout}>
      <div className="page-header">
        <div>
          <h1>Projects</h1>
          <p>Create a new project or join an existing one with its ProjectID.</p>
        </div>
      </div>

      <div className="layout-sidebar">
        <section>
          <div className="section-head">
            <h2>Your projects</h2>
            {!loadingList && <span className="count">{projects.length}</span>}
          </div>

          <Message msg={listError ? { type: "error", text: listError } : null} />

          {loadingList ? (
            <div className="project-grid">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="card project-card">
                  <Skeleton w="55%" h={16} />
                  <Skeleton h={12} />
                  <Skeleton w="75%" h={12} />
                </div>
              ))}
            </div>
          ) : projects.length === 0 ? (
            <div className="card">
              <Empty
                icon={<FolderIcon size={22} />}
                title="No projects yet"
                text="Create your first project, or ask a teammate for a ProjectID to join theirs."
              />
            </div>
          ) : (
            <div className="project-grid">
              {projects.map((p) => (
                <Link
                  key={p.projectId}
                  to={`/projects/${encodeURIComponent(p.projectId)}`}
                  className="card project-card"
                >
                  <div className="project-card-top">
                    <h3>{p.name}</h3>
                    <RoleBadge owner={p.owner === userId} />
                  </div>
                  <p className="desc">{p.description || <span className="muted">No description</span>}</p>
                  <div className="project-card-foot">
                    <code className="id-chip">{p.projectId}</code>
                    {Array.isArray(p.members) && (
                      <span className="foot-members">
                        <UsersIcon size={14} />
                        {p.members.length}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>

        <aside className="sidebar">
          <form className="card" onSubmit={handleCreate}>
            <div className="card-header">
              <div>
                <h2>Create project</h2>
                <p>You'll be the owner.</p>
              </div>
            </div>
            <div className="card-body form-stack">
              <label className="field">
                <span>Name</span>
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Robotics Lab" />
              </label>
              <label className="field">
                <span>ProjectID</span>
                <input className="input" value={newId} onChange={(e) => setNewId(e.target.value)} placeholder="e.g. robotics-01" />
                <small className="hint">Teammates use this to join.</small>
              </label>
              <label className="field">
                <span>Description</span>
                <input
                  className="input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional"
                />
              </label>
              <Message msg={createMsg} />
              <button type="submit" className="btn primary block" disabled={creating}>
                <PlusIcon size={16} />
                {creating ? "Creating…" : "Create project"}
              </button>
            </div>
          </form>

          <form className="card" onSubmit={handleJoin}>
            <div className="card-header">
              <div>
                <h2>Join project</h2>
                <p>Ask the owner for its ProjectID.</p>
              </div>
            </div>
            <div className="card-body form-stack">
              <label className="field">
                <span>ProjectID</span>
                <input
                  className="input"
                  value={existingId}
                  onChange={(e) => setExistingId(e.target.value)}
                  placeholder="Paste a ProjectID"
                />
              </label>
              <Message msg={joinMsg} />
              <button type="submit" className="btn secondary block" disabled={joining}>
                <LinkIcon size={16} />
                {joining ? "Joining…" : "Join project"}
              </button>
            </div>
          </form>
        </aside>
      </div>
    </AppShell>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createProject, getMyProjects, joinProject } from "../api.js";

export default function ProjectsPage({ userId, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [loadingList, setLoadingList] = useState(true);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [newId, setNewId] = useState("");
  const [createMsg, setCreateMsg] = useState({ type: "", text: "" });

  const [existingId, setExistingId] = useState("");
  const [joinMsg, setJoinMsg] = useState({ type: "", text: "" });

  async function refresh() {
    try {
      setProjects(await getMyProjects(userId));
    } catch (err) {
      setJoinMsg({ type: "error", text: err.message });
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
    try {
      const p = await createProject(userId, newId, name, description);
      setCreateMsg({ type: "notice", text: `Created "${p.name}" (${p.projectId})` });
      setName("");
      setDescription("");
      setNewId("");
      refresh();
    } catch (err) {
      setCreateMsg({ type: "error", text: err.message });
    }
  }

  async function handleJoin(e) {
    e.preventDefault();
    setJoinMsg({ type: "", text: "" });
    if (!existingId.trim()) {
      setJoinMsg({ type: "error", text: "Enter a ProjectID" });
      return;
    }
    try {
      const p = await joinProject(userId, existingId);
      setJoinMsg({ type: "notice", text: `Joined "${p.name}"` });
      setExistingId("");
      refresh();
    } catch (err) {
      setJoinMsg({ type: "error", text: err.message });
    }
  }

  return (
    <main className="page wide">
      <div className="topbar">
        <Link to="/">← Home</Link>
        <span>
          Signed in as <b>{userId}</b>{" "}
          <button className="secondary small" onClick={onLogout}>
            Log out
          </button>
        </span>
      </div>

      <div className="columns">
        <form className="card" onSubmit={handleCreate}>
          <h2>Create new project</h2>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            Description
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <label>
            ProjectID
            <input value={newId} onChange={(e) => setNewId(e.target.value)} />
          </label>
          {createMsg.text && <p className={createMsg.type}>{createMsg.text}</p>}
          <button type="submit" className="primary">Create project</button>
        </form>

        <form className="card" onSubmit={handleJoin}>
          <h2>Use existing project</h2>
          <label>
            ProjectID
            <input value={existingId} onChange={(e) => setExistingId(e.target.value)} />
          </label>
          {joinMsg.text && <p className={joinMsg.type}>{joinMsg.text}</p>}
          <button type="submit" className="primary">Join project</button>
        </form>
      </div>

      <div className="card list">
        <h2>Your projects</h2>
        {loadingList ? (
          <p className="subtitle">Loading...</p>
        ) : projects.length === 0 ? (
          <p className="subtitle">No projects yet. Create one or join with a ProjectID.</p>
        ) : (
          <ul>
            {projects.map((p) => (
              <li key={p.projectId}>
                <b>{p.name}</b> <code>{p.projectId}</code>
                {p.description && <div className="subtitle">{p.description}</div>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHardware, getMyProjects } from "../api.js";
import AppShell from "./AppShell.jsx";
import { ChevronRightIcon, CpuIcon, FolderIcon, PlusIcon, UsersIcon } from "./Icons.jsx";
import { Empty, Message, Meter, RoleBadge, Skeleton, SkeletonRows } from "./ui.jsx";

function Stat({ label, value, suffix, icon }) {
  return (
    <div className="card stat">
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">
          {value === null ? <Skeleton w={56} h={30} /> : value}
          {value !== null && value !== "—" && suffix && <small>{suffix}</small>}
        </div>
      </div>
      <div className="stat-icon">{icon}</div>
    </div>
  );
}

export default function HomePage({ userId, onLogout }) {
  const [projects, setProjects] = useState(null);
  const [hardware, setHardware] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMyProjects(userId), getHardware()])
      .then(([p, hw]) => {
        setProjects(p);
        setHardware(hw);
      })
      .catch((err) => setError(err.message));
  }, [userId]);

  const loading = !error && (projects === null || hardware === null);
  const val = (x) => (error ? "—" : loading ? null : x);
  const owned = projects?.filter((p) => p.owner === userId).length ?? 0;
  const totalCap = hardware?.reduce((s, h) => s + h.capacity, 0) ?? 0;
  const totalAvail = hardware?.reduce((s, h) => s + h.availability, 0) ?? 0;

  return (
    <AppShell userId={userId} onLogout={onLogout}>
      <div className="page-header">
        <div>
          <h1>Welcome back, {userId}</h1>
          <p>Here's what's happening across your projects and hardware.</p>
        </div>
        <Link to="/projects" className="btn primary">
          <PlusIcon size={16} />
          New project
        </Link>
      </div>

      <Message msg={error ? { type: "error", text: error } : null} />

      <div className="stats">
        <Stat label="Your projects" icon={<FolderIcon size={20} />} value={val(projects?.length ?? 0)} />
        <Stat label="Projects you own" icon={<UsersIcon size={20} />} value={val(owned)} />
        <Stat label="Units available" icon={<CpuIcon size={20} />} value={val(totalAvail)} suffix={`/ ${totalCap}`} />
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-header">
            <div>
              <h2>Recent projects</h2>
              <p>Projects you own or belong to</p>
            </div>
            <Link to="/projects" className="btn ghost sm">
              View all
              <ChevronRightIcon size={14} />
            </Link>
          </div>
          {loading ? (
            <SkeletonRows />
          ) : projects?.length ? (
            <ul className="rows">
              {projects.slice(0, 5).map((p) => (
                <li key={p.projectId}>
                  <Link className="row" to={`/projects/${encodeURIComponent(p.projectId)}`}>
                    <span className="row-icon">
                      <FolderIcon size={16} />
                    </span>
                    <div className="row-main">
                      <div className="row-title">
                        {p.name}
                        <RoleBadge owner={p.owner === userId} />
                      </div>
                      <div className="row-sub">
                        <code>{p.projectId}</code>
                        {p.description && <> · {p.description}</>}
                      </div>
                    </div>
                    <ChevronRightIcon size={16} className="chev" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <Empty
              icon={<FolderIcon size={22} />}
              title="No projects yet"
              text="Create a project or join one with its ProjectID to start checking out hardware."
              action={
                <Link to="/projects" className="btn primary sm">
                  <PlusIcon size={14} />
                  Get started
                </Link>
              }
            />
          )}
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2>Hardware inventory</h2>
              <p>Units on the shelf across all projects</p>
            </div>
          </div>
          {loading ? (
            <SkeletonRows />
          ) : hardware?.length ? (
            <ul className="rows">
              {hardware.map((h) => (
                <li key={h.hwSetId} className="inv-item">
                  <div className="inv-top">
                    <b>{h.hwSetId}</b>
                    <span>
                      {h.availability} of {h.capacity} available
                    </span>
                  </div>
                  <Meter value={h.availability} max={h.capacity} />
                </li>
              ))}
            </ul>
          ) : (
            <Empty
              icon={<CpuIcon size={22} />}
              title="No hardware sets"
              text="Hardware sets will appear here once they're added."
            />
          )}
        </section>
      </div>
    </AppShell>
  );
}

export default function ProjectsPage({ userId, onLogout }) {
  return (
    <main className="page">
      <div className="card">
        <h1>Welcome, {userId}</h1>
        <p className="subtitle">Projects (Features 2 and 3) will go here.</p>
        <button className="secondary" onClick={onLogout}>
          Log out
        </button>
      </div>
    </main>
  );
}

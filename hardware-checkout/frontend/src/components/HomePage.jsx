import { Link } from "react-router-dom";

export default function HomePage({ userId, onLogout }) {
  return (
    <main className="page">
      <div className="card">
        <h1>Welcome, {userId}</h1>
        <p className="subtitle">What would you like to do?</p>
        <Link to="/projects" className="button primary">
          Create or find a project
        </Link>
        <button className="secondary" onClick={onLogout}>
          Log out
        </button>
      </div>
    </main>
  );
}

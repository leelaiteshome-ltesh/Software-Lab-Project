import { Link, NavLink } from "react-router-dom";
import { LogoIcon, LogOutIcon } from "./Icons.jsx";
import { Avatar } from "./ui.jsx";

export default function AppShell({ userId, onLogout, children }) {
  return (
    <div className="shell">
      <header className="header">
        <div className="header-inner">
          <Link to="/" className="brand">
            <span className="brand-mark">
              <LogoIcon size={17} />
            </span>
            <span className="brand-text">Hardware Checkout</span>
          </Link>

          <nav className="nav">
            <NavLink to="/" end>
              Overview
            </NavLink>
            <NavLink to="/projects">Projects</NavLink>
          </nav>

          <div className="user">
            <Avatar name={userId} size={30} />
            <span className="user-name">{userId}</span>
            <button className="btn ghost icon-only" onClick={onLogout} title="Log out" aria-label="Log out">
              <LogOutIcon size={17} />
            </button>
          </div>
        </div>
      </header>

      <main className="container">{children}</main>
    </div>
  );
}

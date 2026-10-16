import { useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import HomePage from "./components/HomePage.jsx";
import LoginPage from "./components/LoginPage.jsx";
import ProjectsPage from "./components/ProjectsPage.jsx";

export default function App() {
  // Kept in sessionStorage so a page refresh doesn't log the user out.
  const [userId, setUserId] = useState(() => sessionStorage.getItem("userId"));
  const navigate = useNavigate();

  function handleLogin(id) {
    sessionStorage.setItem("userId", id);
    setUserId(id);
    navigate("/");
  }

  function handleLogout() {
    sessionStorage.removeItem("userId");
    setUserId(null);
    navigate("/login");
  }

  return (
    <Routes>
      <Route path="/login" element={userId ? <Navigate to="/" replace /> : <LoginPage onLogin={handleLogin} />} />
      <Route path="/" element={userId ? <HomePage userId={userId} onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
      <Route path="/projects" element={userId ? <ProjectsPage userId={userId} onLogout={handleLogout} /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

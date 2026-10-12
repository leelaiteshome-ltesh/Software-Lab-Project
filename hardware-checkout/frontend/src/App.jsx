import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import ProjectsPage from "./components/ProjectsPage.jsx";

export default function App() {
  const [userId, setUserId] = useState(null);

  return userId ? (
    <ProjectsPage userId={userId} onLogout={() => setUserId(null)} />
  ) : (
    <LoginPage onLogin={setUserId} />
  );
}

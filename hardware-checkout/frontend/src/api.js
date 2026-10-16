const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function post(path, body) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? "Please fill in every field" : data.detail;
    throw new Error(detail || "Something went wrong");
  }
  return data;
}

export const signUp = (userId, password) => post("/users/signup", { userId, password });
export const login = (userId, password) => post("/users/login", { userId, password });

async function get(path) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`);
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((typeof data.detail === "string" && data.detail) || "Something went wrong");
  }
  return data;
}

export const createProject = (userId, projectId, name, description) =>
  post("/projects", { userId, projectId, name, description });
export const joinProject = (userId, projectId) => post("/projects/join", { userId, projectId });
export const getMyProjects = (userId) => get(`/projects?userId=${encodeURIComponent(userId)}`);

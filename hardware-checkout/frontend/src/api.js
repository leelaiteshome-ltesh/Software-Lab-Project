const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(method, path, body) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? "Please check every field" : data.detail;
    throw new Error(detail || "Something went wrong");
  }
  return data;
}

const post = (path, body) => request("POST", path, body);
const get = (path) => request("GET", path);
const del = (path) => request("DELETE", path);
const q = encodeURIComponent;

// Users
export const signUp = (userId, password) => post("/users/signup", { userId, password });
export const login = (userId, password) => post("/users/login", { userId, password });

// Projects
export const createProject = (userId, projectId, name, description) =>
  post("/projects", { userId, projectId, name, description });
export const joinProject = (userId, projectId) => post("/projects/join", { userId, projectId });
export const getMyProjects = (userId) => get(`/projects?userId=${q(userId)}`);
export const getProject = (userId, projectId) => get(`/projects/${q(projectId)}?userId=${q(userId)}`);
export const leaveProject = (userId, projectId) => post(`/projects/${q(projectId)}/leave`, { userId });
export const removeMember = (userId, projectId, memberId) =>
  del(`/projects/${q(projectId)}/members/${q(memberId)}?userId=${q(userId)}`);
export const deleteProject = (userId, projectId) => del(`/projects/${q(projectId)}?userId=${q(userId)}`);

// Hardware
export const getHardwareSets = () => get("/hardware");
export const getProjectHardware = (userId, projectId) =>
  get(`/hardware/projects/${q(projectId)}?userId=${q(userId)}`);
export const checkOut = (userId, projectId, hwSetId, quantity) =>
  post("/hardware/checkout", { userId, projectId, hwSetId, quantity });
export const checkIn = (userId, projectId, hwSetId, quantity) =>
  post("/hardware/checkin", { userId, projectId, hwSetId, quantity });

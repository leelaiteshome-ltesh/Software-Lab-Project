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

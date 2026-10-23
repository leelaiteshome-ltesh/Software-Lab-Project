# Hardware Set Checkout System

FastAPI + MongoDB backend, React (Vite) frontend.

## Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # then paste your MongoDB Atlas URI into .env
uvicorn main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- Run tests: `pytest` (from `backend/`; tests use a fake database, no MongoDB needed)

### Layers

| File | Role |
|---|---|
| `controllers/user_controller.py` | Endpoints only: `POST /users/signup`, `POST /users/login` |
| `services/user_service.py` | Business logic: validation, duplicate check, password encryption |
| `dataservices/user_dataservice.py` | CRUD on the MongoDB `users` collection |
| `entities/user.py` | `User` object (`userId`, `password`) |
| `utils/encryption.py` | Class cipher (reverse + shift, N=3, D=1). Only the password is encrypted |

## Frontend

```
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Set `VITE_API_URL` if the backend isn't on `http://localhost:8000`.

## Notes

- Never commit `backend/.env` (it's in `.gitignore`).
- MongoDB Atlas only accepts IPs on its Network Access list. Add teammates' IPs, or `0.0.0.0/0` during development.

## Projects (Features 2 and 3)

Projects are stored in a **separate MongoDB database** (`MONGODB_PROJECTS_DB_NAME`, default `hardware_checkout_projects`) from users. Projects reference users by `userId` only (no cross-database joins).

Each project has an `owner` (the user who created it) and a `members` list (owner included). Older projects without an `owner` treat their first member as the owner.

**ProjectID rules:** 3-20 characters, starts with a letter, only letters, numbers, `-` and `_`. IDs are unique ignoring case (`Proj-1` and `proj-1` clash), enforced by a unique index on `projectIdLower`. Name is at most 50 characters, description at most 200. The creator's `userId` must be an existing account.

| Endpoint | Who | Purpose |
|---|---|---|
| `POST /projects` | any user | Create a project (creator becomes owner) |
| `POST /projects/join` | any user | Join an existing project by `projectId` |
| `GET /projects?userId=` | any user | List the projects a user belongs to |
| `GET /projects/{projectId}?userId=` | members | Project details |
| `POST /projects/{projectId}/leave` | members (not owner) | Leave a project |
| `DELETE /projects/{projectId}/members/{memberId}?userId=` | owner | Remove a member |
| `DELETE /projects/{projectId}?userId=` | owner | Delete a project (only once all hardware is checked in) |

## Hardware checkout (Feature 4)

Hardware lives in a **third database** (`MONGODB_HARDWARE_DB_NAME`, default `hardware_checkout_hardware`):

- `hardware_sets`: `{hwSetId, name, capacity, availability}`. `HWSet1` and `HWSet2` (capacity 100 each) are created on startup if missing; existing sets are never reset.
- `checkouts`: `{projectId, hwSetId, quantity}`, which tracks how much each project has out.

Hardware is checked out **to a project**; any member can check it in or out. Quantities must be whole numbers of at least 1. A project can't check out more than is available or check in more than it holds. Each update is a single guarded MongoDB operation, so two users can't both take the last units.

| Endpoint | Purpose |
|---|---|
| `GET /hardware` | All sets with capacity and availability |
| `GET /hardware/projects/{projectId}?userId=` | What a project has checked out (members only) |
| `POST /hardware/checkout` | `{userId, projectId, hwSetId, quantity}` |
| `POST /hardware/checkin` | Same body |

Frontend routes: `/login`, `/` (home), `/projects` (create / join / list), `/projects/:projectId` (hardware checkout, members, leave / delete).

**Known limitation:** there are no login tokens yet, so the backend trusts the `userId` the client sends. Owner-only rules are enforced, but a direct API call could claim to be any user.

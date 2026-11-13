# Hardware Set Checkout System

FastAPI + MongoDB backend, React (Vite) frontend.

## Project Diagram 
<img width="1243" height="757" alt="image" src="https://github.com/user-attachments/assets/176456af-e321-40f8-ace6-5ce3850c3915" />

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

Document: `projects {projectId, name, description, owner, members[], createdAt}`

| Endpoint | Purpose |
|---|---|
| `POST /projects` | Create a project (creator becomes owner + first member) |
| `POST /projects/join` | Join an existing project by `projectId` |
| `GET /projects?userId=` | List the projects a user belongs to |
| `GET /projects/{id}?userId=` | Project details (members only) |
| `POST /projects/{id}/leave` | Member leaves (body: `{userId}`) |
| `DELETE /projects/{id}/members/{m}?userId=` | Owner removes member `m` |
| `DELETE /projects/{id}?userId=` | Owner deletes the project |

Rules (`services/project_service.py`):
- ProjectID (no spaces, max 40 chars), name (max 80) and description (max 500) are validated
- The creator must be a real user, and becomes owner + first member
- Only the owner can remove members or delete the project
- The owner can't leave their own project
- Delete is blocked while the project still has hardware checked out

## Hardware

Hardware lives in a **third database** (`MONGODB_HARDWARE_DB_NAME`, default `hardware_checkout_hardware`):

- `hardware_sets {hwSetId, capacity, availability}`: HWSet1 and HWSet2 are created automatically the first time the API is used (capacity 100 each; change with `HWSET1_CAPACITY` / `HWSET2_CAPACITY` in `.env` before first run)
- `checkouts {projectId, hwSetId, quantity}`: how many units each project holds

| Endpoint | Purpose |
|---|---|
| `GET /hardware` | Capacity and availability of every set |
| `GET /hardware/projects/{id}?userId=` | Every set + how many units this project holds |
| `POST /hardware/checkout` | Body: `{userId, projectId, hwSetId, quantity}` |
| `POST /hardware/checkin` | Same body |

Rules (`services/hardware_service.py`):
- Members only
- Quantity must be a whole number >= 1
- Can't take more than is available
- Can't return more than the project holds

Availability and project holdings are updated with conditional MongoDB updates, so two people checking out at the same time can't push either below 0.

## Frontend routes

- `/login`: sign in / new user
- `/`: home
- `/projects`: create, join, and list your projects (with Owner / Member badge)
- `/projects/:projectId`: hardware table (check out / check in), members list, remove member (owner), delete project (owner), leave project (member)

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

| Endpoint | Purpose |
|---|---|
| `POST /projects` | Create a project (creator becomes first member) |
| `POST /projects/join` | Join an existing project by `projectId` |
| `GET /projects?userId=` | List the projects a user belongs to |

Frontend routes: `/login`, `/` (home, with link to projects), `/projects` (create / join / list). Run `npm install` again, since `react-router-dom` was added.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.hardware_controller import router as hardware_router
from controllers.project_controller import router as project_router
from controllers.user_controller import router as user_router
from dataservices.hardware_dataservice import HardwareDataService
from dataservices.project_dataservice import ProjectDataService
from db import get_hardware_database, get_projects_database
from entities.hardware import DEFAULT_HARDWARE_SETS


@asynccontextmanager
async def lifespan(app):
    # Set up indexes and default hardware sets. Don't crash the server if
    # MongoDB is unreachable; requests will report the error instead.
    try:
        ProjectDataService(get_projects_database()["projects"]).ensure_indexes()
        HardwareDataService(get_hardware_database()).ensure_defaults(DEFAULT_HARDWARE_SETS)
    except Exception as e:
        print(f"WARNING: database setup failed: {e}")
    yield


app = FastAPI(
    title="Hardware Set Checkout System API",
    description="Swagger UI for testing endpoints. Features: users, projects (owner/members), hardware checkout.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(project_router)
app.include_router(hardware_router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.project_controller import router as project_router
from controllers.user_controller import router as user_router

app = FastAPI(
    title="Hardware Set Checkout System API",
    description="Swagger UI for testing endpoints. Features: users (sign up, login) and projects (create, join, list).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(project_router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}

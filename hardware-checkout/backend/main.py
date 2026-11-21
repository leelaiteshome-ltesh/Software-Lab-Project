from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from controllers.hardware_controller import router as hardware_router
from controllers.project_controller import router as project_router
from controllers.user_controller import router as user_router

app = FastAPI(
    title="Hardware Set Checkout System API",
    description="Swagger UI for testing endpoints. Features: users (sign up, login), projects (create, join, manage members) and hardware (check out / check in).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (user_router, project_router, hardware_router):
    app.include_router(router)
    # Same endpoints under /api for the hosted site, where the React app is
    # served from this server and page URLs like /projects belong to React.
    app.include_router(router, prefix="/api", include_in_schema=False)


@app.get("/", tags=["Health"])
@app.get("/api/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ---------- hosted frontend ----------
# When the React app has been built (frontend/dist), serve it from this server
# so the whole app runs at one URL. Locally, without a build, nothing changes.

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
API_PATHS = ("/api", "/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def serve_frontend(request: Request, call_next):
    path = request.url.path
    is_page_load = request.method == "GET" and "text/html" in request.headers.get("accept", "")
    if FRONTEND_DIST.is_dir() and request.method == "GET" and not path.startswith(API_PATHS):
        file = (FRONTEND_DIST / path.lstrip("/")).resolve()
        if path != "/" and file.is_file() and FRONTEND_DIST in file.parents:
            return FileResponse(file)
        if is_page_load:
            # React handles /login, /projects, /projects/<id>, etc.
            return FileResponse(FRONTEND_DIST / "index.html")
    return await call_next(request)

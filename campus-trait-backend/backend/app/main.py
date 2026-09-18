"""
Campus Trait API — FastAPI backend.

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Interactive docs then live at http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine, SessionLocal
from .routers import auth, items, wishlist, messages, users
from .seed import run_seed
from .utils import UPLOAD_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Campus Trait API",
    description="Backend for the Campus Trait campus marketplace — listings, wishlist, messaging and auth.",
    version="1.0.0",
)

# Allow the frontend (served from any origin, e.g. a static file or a dev server)
# to call this API directly from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(wishlist.router)
app.include_router(messages.router)
app.include_router(users.router)


@app.on_event("startup")
def seed_on_startup():
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}

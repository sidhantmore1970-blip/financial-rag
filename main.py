from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.database import setup_db
from routes import auth, documents, roles, rag


@asynccontextmanager
async def startup(app: FastAPI):
    setup_db()
    yield


app = FastAPI(title="Financial Docs API", lifespan=startup)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(roles.router, prefix="", tags=["roles"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])


@app.get("/")
def home():
    return {"msg": "API is running"}

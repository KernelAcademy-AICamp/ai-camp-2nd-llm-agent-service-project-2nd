from fastapi import FastAPI
from app.routers.documents import router as documents_router

app = FastAPI(title="LSSP Documents Module v2.05 (reference)")
app.include_router(documents_router)

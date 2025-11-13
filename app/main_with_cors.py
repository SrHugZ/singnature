from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, organizations, members, signature_templates, signatures, banners, analytics, uploads
from app.db.database import engine
from app.db import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# CORS - CRÍTICO PARA FRONTEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(organizations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])
app.include_router(members.router, prefix=f"{settings.API_V1_STR}/members", tags=["members"])
app.include_router(signature_templates.router, prefix=f"{settings.API_V1_STR}/signature-templates", tags=["signature-templates"])
app.include_router(signatures.router, prefix=f"{settings.API_V1_STR}/signatures", tags=["signatures"])
app.include_router(banners.router, prefix=f"{settings.API_V1_STR}/banners", tags=["banners"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_STR}/uploads", tags=["uploads"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}

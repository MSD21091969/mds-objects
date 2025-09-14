from fastapi import FastAPI
from src.components.casefile_management.api import router as casefile_router

app = FastAPI()

# Voeg de casefile-routes toe aan de hoofapplicatie
app.include_router(casefile_router, prefix="/api/v1", tags=["Casefile Management"])

@app.get("/")
def read_root():
    return {"status": "MDS7 Rebuild API is running"}

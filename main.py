from fastapi import FastAPI
from api.health import router as health_router
from api.auth import router as auth_router

app = FastAPI(title="Chatbot API")

app.include_router(health_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "API working"}   
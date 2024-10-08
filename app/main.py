from fastapi import FastAPI
from .server_management import router as server_management_router
from .auth import router as auth_router
from . import stripe_payments

app = FastAPI()

# Include routes for authentication and server management
app.include_router(auth_router, prefix="/auth")
app.include_router(server_management_router, prefix="/servers")
app.include_router(stripe_payments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Minecraft Server Hosting API!"}


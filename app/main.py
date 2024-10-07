from fastapi import FastAPI
from .server_management import router as server_management_router
from .auth import router as auth_router
from .payment import router as payment_router  # Import payment_router correctly
from .models import Payment

app = FastAPI()

# Include routes for authentication, server management, and payments
app.include_router(auth_router, prefix="/auth")
app.include_router(server_management_router, prefix="/servers")
app.include_router(payment_router, prefix="/payments", tags=["payments"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Minecraft Server Hosting API!"}


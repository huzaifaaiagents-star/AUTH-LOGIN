from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import Request


# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PORT = os.getenv("PORT")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")

@app.get("/")
def read_root():
    return {"status": "ok"}

# pyrefly: ignore [missing-import]

class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None

@app.post("/auth/signup")
def signup(payload: AuthRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(status_code=201, content={"user": response.user.model_dump(mode="json")})


@app.post("/auth/login")
def login(payload: AuthRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return JSONResponse(status_code=200, content={
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token
    })

@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def protected_profile(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer ") or len(auth_header.split(" ")) < 2:
        raise HTTPException(status_code=401, detail="Access token required")

    token = auth_header.split(" ")[1]

    try:
        response = supabase.auth.get_user(token)
        user = response.user
        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at
        }
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"}
        )    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=True)
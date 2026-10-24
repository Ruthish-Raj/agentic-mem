from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .. import database
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
async def signup(req: SignupRequest):
    existing = await database.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(req.password)
    user = await database.create_user(req.email, req.name, hashed)
    token = create_access_token({"sub": user["_id"], "email": user["email"], "name": user["name"]})
    return {"access_token": token, "token_type": "bearer", "name": user["name"], "email": user["email"]}


@router.post("/login")
async def login(req: LoginRequest):
    user = await database.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id, "email": user["email"], "name": user["name"]})
    return {"access_token": token, "token_type": "bearer", "name": user["name"], "email": user["email"]}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "name": current_user["name"],
        "_id": str(current_user["_id"]),
    }

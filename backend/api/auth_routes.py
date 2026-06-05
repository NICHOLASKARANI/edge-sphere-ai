from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict
from auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_user, get_current_active_user, User
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "company": user["company"],
            "role": user["role"]
        }
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    # Verify refresh token and issue new access token
    from auth import jwt, SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username = payload.get("sub")
        new_access_token = create_access_token(data={"sub": username})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    # In production, add token to blacklist
    return {"message": "Successfully logged out"}
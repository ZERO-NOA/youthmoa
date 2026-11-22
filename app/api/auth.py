
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

import sqlite3

from app.db.database import (
    create_user,
    get_user_by_username,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["회원 인증"]
)


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=4,
        max_length=30
    )

    password: str = Field(
        min_length=8,
        max_length=100
    )

    display_name: str = Field(
        min_length=1,
        max_length=50
    )


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(request: RegisterRequest):
    """
    회원가입
    """
    existing_user = get_user_by_username(
        request.username
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="이미 사용 중인 로그인 ID입니다."
        )

    password_hash = hash_password(
        request.password
    )

    try:
        user_id = create_user(
            username=request.username,
            password_hash=password_hash,
            display_name=request.display_name
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="이미 사용 중인 로그인 ID입니다."
        )

    return {
        "success": True,
        "message": "회원가입이 완료되었습니다.",
        "user": {
            "id": user_id,
            "username": request.username,
            "display_name": request.display_name,
        },
    }


@router.post("/login")
def login(request: LoginRequest):
    """
    로그인 및 JWT 발급
    """
    user = get_user_by_username(
        request.username
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="로그인 ID 또는 비밀번호가 올바르지 않습니다."
        )

    password_valid = verify_password(
        request.password,
        user["password_hash"]
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="로그인 ID 또는 비밀번호가 올바르지 않습니다."
        )

    access_token = create_access_token(
        user["id"]
    )

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
        },
    }


@router.get("/me")
def get_me(
    user=Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회
    """
    return {
        "success": True,
        "user": user,
    }

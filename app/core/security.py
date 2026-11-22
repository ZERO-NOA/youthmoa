
import os
import hashlib
import secrets

from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.database import get_user_by_id


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY가 .env에 설정되지 않았습니다."
    )


security_scheme = HTTPBearer()


def hash_password(password):
    """
    비밀번호를 PBKDF2 방식으로 해시한다.
    """
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """
    입력한 비밀번호와 저장된 해시를 비교한다.
    """
    try:
        salt, saved_hash = stored_hash.split("$", 1)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200000
        ).hex()

        return secrets.compare_digest(
            password_hash,
            saved_hash
        )

    except ValueError:
        return False


def create_access_token(user_id):
    """
    사용자 ID를 포함한 JWT 액세스 토큰 생성
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security_scheme
    )
):
    """
    Authorization 헤더의 JWT를 검증하고
    로그인한 사용자 정보를 반환한다.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="토큰에 사용자 정보가 없습니다."
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="로그인 토큰이 만료되었습니다."
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 로그인 토큰입니다."
        )

    user = get_user_by_id(int(user_id))

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="사용자를 찾을 수 없습니다."
        )

    return user

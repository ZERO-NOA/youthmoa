
from fastapi import FastAPI

from app.api.kdata_schedules import router as kdata_router

from app.db.database import initialize_database

from app.api.certifications import router as certifications_router

from app.api.auth import router as auth_router

app = FastAPI(
    title="자격증 로드맵 API",
    description="학생 맞춤형 자격증 로드맵 서비스",
    version="1.0.0",
)

# 데이터베이스 테이블 자동 생성
initialize_database()

# API 라우터 등록
app.include_router(kdata_router)


@app.get("/")
def home():
    return {
        "message": "자격증 로드맵 백엔드 서버가 정상적으로 실행 중입니다."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


# 자격증 검색 API 연결
app.include_router(kdata_router)
app.include_router(certifications_router)

# 회원 인증 API 연결
app.include_router(auth_router)
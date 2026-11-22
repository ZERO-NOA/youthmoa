
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user

from app.services.roadmap_service import (
    CERTIFICATION_KEYWORDS,
    generate_selected_certification_roadmap,
)

from app.db.database import (
    save_user_certification,
    get_user_certifications,
    delete_user_certification,
    get_roadmap_tasks,
)


router = APIRouter(
    prefix="/api/certifications",
    tags=["자격증 선택"]
)


# 선택 가능한 자격증 목록
CERTIFICATION_CATALOG = [
    {
        "cert_id": "ADSP",
        "cert_name": "데이터분석 준전문가(ADsP)"
    },
    {
        "cert_id": "BIGDATA_ANALYST",
        "cert_name": "빅데이터분석기사"
    },
    {
        "cert_id": "SQLD",
        "cert_name": "SQL 개발자(SQLD)"
    },
    {
        "cert_id": "INFORMATION_PROCESSING",
        "cert_name": "정보처리기사"
    },
]


class CertificationSelectRequest(BaseModel):
    cert_id: str


# --------------------------------------------------
# 선택 가능한 자격증 목록 조회
# --------------------------------------------------
@router.get("")
def get_certification_catalog():
    return {
        "success": True,
        "total": len(CERTIFICATION_CATALOG),
        "items": CERTIFICATION_CATALOG,
    }


# --------------------------------------------------
# 자격증 선택 및 저장
# --------------------------------------------------
@router.post("/select")
def select_certification(
    request: CertificationSelectRequest,
    user=Depends(get_current_user)
):
    user_id = str(user["id"])

    certification = next(
        (
            item
            for item in CERTIFICATION_CATALOG
            if item["cert_id"] == request.cert_id
        ),
        None
    )

    if certification is None:
        raise HTTPException(
            status_code=404,
            detail="등록되지 않은 자격증입니다."
        )

    inserted = save_user_certification(
        user_id=user_id,
        cert_id=certification["cert_id"],
        cert_name=certification["cert_name"]
    )

    return {
        "success": True,
        "message": (
            "자격증이 등록되었습니다."
            if inserted
            else "이미 등록된 자격증입니다."
        ),
        "certification": certification,
    }


# --------------------------------------------------
# 로그인한 사용자의 자격증 조회
# --------------------------------------------------
@router.get("/my")
def get_my_certifications(
    user=Depends(get_current_user)
):
    user_id = str(user["id"])

    certifications = get_user_certifications(
        user_id=user_id
    )

    return {
        "success": True,
        "user_id": user_id,
        "total": len(certifications),
        "items": certifications,
    }


# --------------------------------------------------
# 로그인한 사용자의 자격증 삭제
# --------------------------------------------------
@router.delete("/{cert_id}")
def delete_certification(
    cert_id: str,
    user=Depends(get_current_user)
):
    user_id = str(user["id"])

    deleted = delete_user_certification(
        user_id=user_id,
        cert_id=cert_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="선택한 자격증을 찾을 수 없습니다."
        )

    return {
        "success": True,
        "message": "자격증이 삭제되었습니다."
    }


# --------------------------------------------------
# 로그인한 사용자의 로드맵 생성 및 동기화
# --------------------------------------------------
@router.post("/my/roadmap/sync")
def sync_my_roadmap(
    user=Depends(get_current_user)
):
    user_id = str(user["id"])

    try:
        result = generate_selected_certification_roadmap(
            user_id=user_id
        )

        if result["selected_count"] == 0:
            raise HTTPException(
                status_code=400,
                detail="먼저 자격증을 선택해주세요."
            )

        return {
            "success": True,
            **result,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# 로그인한 사용자의 로드맵 조회
# --------------------------------------------------
@router.get("/my/roadmap")
def get_my_roadmap(
    user=Depends(get_current_user)
):
    user_id = str(user["id"])

    try:
        selected_certifications = get_user_certifications(
            user_id=user_id
        )

        if not selected_certifications:
            return {
                "success": True,
                "total": 0,
                "items": [],
                "message": "선택한 자격증이 없습니다.",
            }

        tasks = get_roadmap_tasks(
            user_id=user_id
        )

        selected_keywords = []

        for certification in selected_certifications:
            keywords = CERTIFICATION_KEYWORDS.get(
                certification["cert_id"],
                [certification["cert_name"]]
            )

            selected_keywords.extend(keywords)

        filtered_tasks = []

        for task in tasks:
            exam_name = str(
                task.get("exam_name", "")
            )

            if any(
                keyword.lower() in exam_name.lower()
                for keyword in selected_keywords
            ):
                filtered_tasks.append(task)

        return {
            "success": True,
            "total": len(filtered_tasks),
            "items": filtered_tasks,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

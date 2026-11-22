
import requests

from fastapi import APIRouter, HTTPException, Query

from app.services.qualification_client import (
    get_qualification_list,
)

router = APIRouter(
    prefix="/api/qualifications",
    tags=["자격증 검색"],
)


@router.get("")
def search_qualifications(
    keyword: str = Query(default=""),
):
    try:
        result = get_qualification_list(
            page=1,
            per_page=100,
        )

        qualifications = result.get("data", [])

        # 검색어가 입력된 경우 종목명으로 필터링
        if keyword:
            filtered = []

            for item in qualifications:
                name = item.get("종목명") or ""

                if keyword.lower() in name.lower():
                    filtered.append(item)

            qualifications = filtered

        return {
            "total": len(qualifications),
            "items": qualifications,
        }

    except requests.exceptions.RequestException as e:
        print("외부 API 요청 오류:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="국가자격 API 호출에 실패했습니다.",
        )

    except Exception as e:
        print("자격증 검색 내부 오류:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="자격증 검색 처리 중 오류가 발생했습니다.",
        )


import traceback
import requests

from pydantic import BaseModel

from app.services.roadmap_service import generate_roadmap

from app.db.database import (
    save_roadmap_tasks,
    get_roadmap_tasks,
    update_roadmap_task_status,
)

from app.services.roadmap_service import generate_roadmap

from app.db.database import (
    save_schedules,
    get_saved_schedules,
    get_schedule_count,
)

from fastapi import APIRouter, HTTPException, Query

from app.services.kdata_schedule_service import (
    get_future_kdata_schedules,
)


router = APIRouter(
    prefix="/api/kdata",
    tags=["K-DATA 시험 일정"],
)


@router.get("/schedules")
def search_kdata_schedules(
    keyword: str = Query(
        default="",
        description="검색할 자격증 이름 (예: ADsP, SQLD)",
    ),
):
    """
    K-DATA 데이터 자격검정 시험 일정 조회

    - 오늘 이후의 시험 일정만 반환
    - 자격증 이름으로 검색 가능
    - 시험장소 정보는 반환하지 않음
    """

    try:
        # 미래 시험 일정 조회
        schedules = get_future_kdata_schedules(
            keyword=keyword,
        )

        # 검색 결과 반환
        return {
            "source": "K-DATA",
            "keyword": keyword,
            "total": len(schedules),
            "items": schedules,
        }

    except requests.exceptions.RequestException as e:
        print("K-DATA API 요청 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="K-DATA 시험 일정 API 호출에 실패했습니다.",
        )

    except ValueError as e:
        print("K-DATA 데이터 처리 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="K-DATA 시험 일정 데이터 처리 중 오류가 발생했습니다.",
        )

    except Exception as e:
        print("시험 일정 처리 중 예상하지 못한 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="시험 일정 처리 중 오류가 발생했습니다.",
        )


@router.post("/sync")
def sync_kdata_schedules(
    keyword: str = Query(
        default="",
        description="동기화할 자격증 이름",
    ),
):
    """
    K-DATA 시험 일정을 API에서 가져와
    SQLite 데이터베이스에 저장한다.
    """

    try:
        schedules = get_future_kdata_schedules(
            keyword=keyword,
        )

        saved_count = save_schedules(
            schedules,
            source="K-DATA",
        )

        return {
            "message": "K-DATA 시험 일정 동기화 완료",
            "keyword": keyword,
            "received": len(schedules),
            "saved": saved_count,
            "database_total": get_schedule_count(),
        }

    except Exception as e:
        print("K-DATA 일정 동기화 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="시험 일정 동기화 중 오류가 발생했습니다.",
        )

@router.get("/saved-schedules")
def search_saved_schedules(
    keyword: str = Query(
        default="",
        description="저장된 시험 일정 검색",
    ),
):
    """
    SQLite에 저장된 미래 시험 일정 조회
    """

    try:
        schedules = get_saved_schedules(
            keyword=keyword,
        )

        return {
            "source": "SQLite",
            "keyword": keyword,
            "total": len(schedules),
            "items": schedules,
        }

    except Exception as e:
        print("저장된 시험 일정 조회 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="저장된 시험 일정 조회 중 오류가 발생했습니다.",
        )


@router.get("/roadmap")
def get_exam_roadmap(
    keyword: str = Query(
        default="",
        description="자격증 이름",
    ),
):
    """
    저장된 시험 일정으로 로드맵 생성
    """

    try:
        roadmap = generate_roadmap(
            keyword=keyword
        )

        return {
            "source": "SQLite",
            "keyword": keyword,
            "total": len(roadmap),
            "items": roadmap,
        }

    except Exception as e:
        print("로드맵 생성 오류:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="시험 로드맵 생성 중 오류가 발생했습니다.",
        )


class RoadmapTaskStatusRequest(BaseModel):
    status: str


@router.post("/roadmap/tasks/sync")
def sync_roadmap_tasks(
    keyword: str = Query(default="")
):
    """
    생성된 로드맵 과제를 SQLite에 저장한다.
    """
    try:
        tasks = generate_roadmap(keyword)

        saved_count = save_roadmap_tasks(
            tasks,
            user_id="demo-user"
        )

        return {
            "success": True,
            "message": "로드맵 과제가 저장되었습니다.",
            "saved_count": saved_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/roadmap/tasks")
def read_saved_roadmap_tasks(
    keyword: str = Query(default="")
):
    """
    SQLite에 저장된 로드맵 과제를 조회한다.
    """
    try:
        tasks = get_roadmap_tasks(
            user_id="demo-user",
            keyword=keyword
        )

        return {
            "success": True,
            "total": len(tasks),
            "items": tasks,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.patch("/roadmap/tasks/{task_id}")
def change_roadmap_task_status(
    task_id: str,
    request: RoadmapTaskStatusRequest
):
    """
    과제의 진행 상태를 변경한다.
    """
    try:
        updated = update_roadmap_task_status(
            task_id=task_id,
            status=request.status,
            user_id="demo-user"
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="해당 과제를 찾을 수 없습니다."
            )

        return {
            "success": True,
            "task_id": task_id,
            "status": request.status,
            "message": "과제 상태가 변경되었습니다.",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

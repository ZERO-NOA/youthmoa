
from datetime import date, datetime

from app.services.kdata_client import (
    get_kdata_schedule_data,
)


def parse_date(value):
    """
    API 날짜 문자열을 date 객체로 변환한다.

    지원 형식:
    - YYYY-MM-DD
    - YYYYMMDD
    - ISO datetime
    """

    if not value:
        return None

    value = str(value).strip()

    # ISO 날짜 또는 datetime 처리
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError:
        pass

    # 일반 날짜 형식 처리
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(
                value,
                fmt,
            ).date()
        except ValueError:
            continue

    return None


def normalize_schedule(item):
    """
    K-DATA 원본 데이터를
    로드맵에서 사용할 일정 형식으로 변환한다.

    시험장소와 순번은 반환하지 않는다.
    """

    return {
        "시험명": item.get("시험명"),
        "시험구분": item.get("시험구분"),
        "회차": item.get("회차"),
        "시험일": item.get("시험일"),
        "시험시작시간": item.get("시험시작시간"),
        "접수시작일": item.get("접수시작일"),
        "접수마감일": item.get("접수마감일"),
        "합격자발표일": item.get("합격자발표일"),
        "시험유형": item.get("시험유형"),
    }


def make_schedule_key(item):
    """
    동일한 시험 일정인지 판단하기 위한 고유 키를 만든다.

    시험장소가 달라도 같은 시험 일정이면
    중복으로 처리한다.
    """

    return (
        str(item.get("시험명", "")).strip(),
        str(item.get("시험구분", "")).strip(),
        str(item.get("회차", "")).strip(),
        str(item.get("시험일", "")).strip(),
        str(item.get("시험시작시간", "")).strip(),
        str(item.get("시험유형", "")).strip(),
        str(item.get("접수시작일", "")).strip(),
        str(item.get("접수마감일", "")).strip(),
        str(item.get("합격자발표일", "")).strip(),
    )


def get_future_kdata_schedules(keyword: str = ""):
    """
    K-DATA 시험 일정 조회 및 정리

    기능:
    1. 오늘 이후 시험 일정만 추출
    2. 자격증 이름 검색
    3. 중복 일정 제거
    4. 시험일 오름차순 정렬
    5. 불필요한 장소 정보 제거
    """

    today = date.today()

    # K-DATA 원본 데이터 조회
    raw_data = get_kdata_schedule_data()

    schedules = []
    seen_keys = set()

    search_keyword = keyword.strip().lower()

    for item in raw_data:

        # 시험명 검색
        exam_name = str(
            item.get("시험명", "")
        ).strip()

        if search_keyword:
            if search_keyword not in exam_name.lower():
                continue

        # 시험 날짜 변환
        exam_date = parse_date(
            item.get("시험일")
        )

        # 날짜가 없거나 잘못된 데이터 제외
        if exam_date is None:
            continue

        # 오늘 이전 시험 제외
        if exam_date < today:
            continue

        # 필요한 정보만 추출
        schedule = normalize_schedule(item)

        # 중복 확인
        schedule_key = make_schedule_key(
            schedule
        )

        if schedule_key in seen_keys:
            continue

        seen_keys.add(schedule_key)

        schedules.append(schedule)

    # 시험일 기준 오름차순 정렬
    schedules.sort(
        key=lambda item: (
            parse_date(item.get("시험일"))
            or date.max,
            str(item.get("시험시작시간", "")),
            str(item.get("시험명", "")),
        )
    )

    return schedules


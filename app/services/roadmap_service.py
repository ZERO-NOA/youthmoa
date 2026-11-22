
from datetime import date, timedelta

from app.db.database import (
    get_saved_schedules,
    get_user_certifications,
    save_roadmap_tasks,
    get_roadmap_tasks,
)


def parse_date(value):
    """
    YYYY-MM-DD 형식의 날짜를 date 객체로 변환
    """

    if not value:
        return None

    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def make_task(
    exam_name,
    exam_date,
    task_date,
    task_type,
    title,
    description,
    is_notification=False,
):
    """
    로드맵 작업 데이터 생성
    """

    return {
        "exam_name": exam_name,
        "exam_date": exam_date.isoformat(),
        "task_date": task_date.isoformat(),
        "task_type": task_type,
        "title": title,
        "description": description,
        "is_notification": is_notification,
        "status": "pending",
    }


def generate_roadmap_for_schedule(schedule):
    """
    시험 일정 하나를 기반으로
    준비 작업과 알림 예정일을 생성한다.
    """

    today = date.today()

    exam_name = schedule.get("시험명", "")
    exam_date = parse_date(schedule.get("시험일"))

    if not exam_date:
        return []

    if exam_date < today:
        return []

    tasks = []

    # 주요 날짜
    registration_start = parse_date(
        schedule.get("접수시작일")
    )

    registration_end = parse_date(
        schedule.get("접수마감일")
    )

    result_date = parse_date(
        schedule.get("합격자발표일")
    )

    # ---------------------------------
    # 1. 원서 접수 시작일
    # ---------------------------------

    if registration_start and registration_start >= today:

        tasks.append(
            make_task(
                exam_name,
                exam_date,
                registration_start,
                "registration",
                "원서 접수 시작",
                f"{exam_name} 원서 접수를 시작할 수 있습니다.",
                True,
            )
        )

    # ---------------------------------
    # 2. 원서 접수 마감일
    # ---------------------------------

    if registration_end and registration_end >= today:

        tasks.append(
            make_task(
                exam_name,
                exam_date,
                registration_end,
                "registration_deadline",
                "원서 접수 마감",
                f"{exam_name} 원서 접수 마감일입니다. 접수 여부를 확인하세요.",
                True,
            )
        )

    # ---------------------------------
    # 3. 시험 준비 작업
    # ---------------------------------

    preparation_plan = [
        (
            30,
            "학습 계획 수립",
            "시험 범위를 확인하고 학습 계획을 세우세요.",
        ),
        (
            14,
            "핵심 내용 복습",
            "중요 개념과 자주 출제되는 내용을 복습하세요.",
        ),
        (
            7,
            "기출문제 및 모의시험",
            "기출문제와 모의시험을 통해 실력을 점검하세요.",
        ),
        (
            3,
            "취약 부분 집중 학습",
            "틀린 문제와 부족한 부분을 집중적으로 보완하세요.",
        ),
        (
            1,
            "시험 전 최종 점검",
            "시험 준비물과 시험 시간을 확인하고 충분히 휴식하세요.",
        ),
    ]

    for days_before, title, description in preparation_plan:

        task_date = exam_date - timedelta(
            days=days_before
        )

        # 오늘 이전 작업은 생성하지 않는다.
        if task_date < today:
            continue

        tasks.append(
            make_task(
                exam_name,
                exam_date,
                task_date,
                "study",
                title,
                description,
                False,
            )
        )

    # ---------------------------------
    # 4. 시험일
    # ---------------------------------

    tasks.append(
        make_task(
            exam_name,
            exam_date,
            exam_date,
            "exam",
            "자격증 시험일",
            f"{exam_name} 시험에 응시하세요.",
            True,
        )
    )

    # ---------------------------------
    # 5. 합격자 발표일
    # ---------------------------------

    if result_date and result_date >= today:

        tasks.append(
            make_task(
                exam_name,
                exam_date,
                result_date,
                "result",
                "합격자 발표 확인",
                f"{exam_name} 합격자 발표를 확인하세요.",
                True,
            )
        )

    # 날짜순 정렬
    tasks.sort(
        key=lambda item: item["task_date"]
    )

    return tasks


def generate_roadmap(keyword=""):
    """
    SQLite에 저장된 시험 일정을 기반으로
    전체 로드맵을 생성한다.
    """

    schedules = get_saved_schedules(
        keyword=keyword
    )

    roadmap = []

    for schedule in schedules:

        tasks = generate_roadmap_for_schedule(
            schedule
        )

        roadmap.extend(tasks)

    roadmap.sort(
        key=lambda item: item["task_date"]
    )

    return roadmap


# 자격증 ID별 시험명 검색 키워드
CERTIFICATION_KEYWORDS = {
    "ADSP": [
        "ADsP",
        "데이터분석 준전문가",
        "데이터 분석 준전문가",
    ],
    "BIGDATA_ANALYST": [
        "빅데이터분석기사",
    ],
    "SQLD": [
        "SQLD",
        "SQL 개발자",
    ],
    "INFORMATION_PROCESSING": [
        "정보처리기사",
    ],
}


def generate_selected_certification_roadmap(
    user_id="demo-user"
):
    """
    사용자가 선택한 자격증에 해당하는
    시험 일정만 찾아 로드맵 과제를 생성한다.
    """

    # 사용자가 선택한 자격증 조회
    selected_certifications = get_user_certifications(
        user_id=user_id
    )

    if not selected_certifications:
        return {
            "selected_count": 0,
            "schedule_count": 0,
            "task_count": 0,
            "message": "선택한 자격증이 없습니다.",
        }

    # 저장된 시험 일정 조회
    schedules = get_saved_schedules()

    selected_schedules = []

    for certification in selected_certifications:
        cert_id = certification["cert_id"]

        keywords = CERTIFICATION_KEYWORDS.get(
            cert_id,
            [certification["cert_name"]]
        )

        for schedule in schedules:
            exam_name = str(
                schedule.get("exam_name", "")
            )

            # 선택한 자격증의 시험 일정인지 확인
            if any(
                keyword.lower() in exam_name.lower()
                for keyword in keywords
            ):
                selected_schedules.append(schedule)

    # 중복 일정 제거
    unique_schedules = {}

    for schedule in selected_schedules:
        schedule_key = (
            schedule.get("exam_name", ""),
            schedule.get("exam_date", ""),
            schedule.get("exam_time", ""),
            schedule.get("exam_type", ""),
        )

        unique_schedules[schedule_key] = schedule

    selected_schedules = list(
        unique_schedules.values()
    )

    # 기존 로드맵 생성 함수 사용
    generated_tasks = []

    for schedule in selected_schedules:
        tasks = generate_roadmap_for_schedule(
            schedule
        )

        generated_tasks.extend(tasks)

    # 생성된 과제를 SQLite에 저장
    saved_count = save_roadmap_tasks(
        generated_tasks,
        user_id=user_id
    )

    return {
        "selected_count": len(selected_certifications),
        "schedule_count": len(selected_schedules),
        "task_count": saved_count,
        "message": "선택한 자격증의 로드맵 생성 완료",
    }

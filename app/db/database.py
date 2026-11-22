
import sqlite3
import hashlib

from pathlib import Path
from datetime import date, datetime


# =========================================================
# 1. 데이터베이스 경로 설정
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "roadmap.db"


# =========================================================
# 2. 데이터베이스 연결
# =========================================================

def get_connection():
    """
    SQLite 데이터베이스 연결
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# 3. 데이터베이스 테이블 초기화
# =========================================================


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 시험 일정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_key TEXT UNIQUE,
            exam_name TEXT,
            exam_date TEXT,
            exam_time TEXT,
            registration_start TEXT,
            registration_end TEXT,
            result_date TEXT,
            exam_type TEXT,
            exam_round TEXT
        )
    """)

    # 2. 로드맵 작업 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roadmap_tasks (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            certification_name TEXT,
            task_name TEXT,
            task_date TEXT,
            status TEXT DEFAULT 'pending',
            description TEXT
        )
    """)

    # 3. 사용자별 자격증 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            certification_name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, certification_name)
        )
    """)

    # 4. 회원 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 모든 테이블 생성이 끝난 후 저장 및 연결 종료
    conn.commit()
    conn.close()



# =========================================================
# 4. 시험 일정 데이터 저장
# =========================================================

def make_schedule_key(schedule):
    """
    시험 일정의 고유 키 생성
    """
    raw = "|".join([
        str(schedule.get("exam_name", "")),
        str(schedule.get("exam_category", "")),
        str(schedule.get("exam_round", "")),
        str(schedule.get("exam_date", "")),
        str(schedule.get("exam_time", "")),
        str(schedule.get("exam_type", "")),
    ])

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def save_schedules(schedules, source="K-DATA"):
    """
    시험 일정 목록을 SQLite에 저장한다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    saved_count = 0

    try:
        for schedule in schedules:
            schedule_key = make_schedule_key(schedule)

            cursor.execute("""
                INSERT INTO exam_schedules (
                    schedule_key,
                    source,
                    exam_name,
                    exam_category,
                    exam_round,
                    exam_date,
                    exam_time,
                    registration_start,
                    registration_end,
                    result_date,
                    exam_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(schedule_key) DO UPDATE SET
                    source = excluded.source,
                    exam_name = excluded.exam_name,
                    exam_category = excluded.exam_category,
                    exam_round = excluded.exam_round,
                    exam_date = excluded.exam_date,
                    exam_time = excluded.exam_time,
                    registration_start = excluded.registration_start,
                    registration_end = excluded.registration_end,
                    result_date = excluded.result_date,
                    exam_type = excluded.exam_type
            """, (
                schedule_key,
                source,
                schedule.get("exam_name", ""),
                schedule.get("exam_category", ""),
                schedule.get("exam_round", ""),
                schedule.get("exam_date", ""),
                schedule.get("exam_time", ""),
                schedule.get("registration_start", ""),
                schedule.get("registration_end", ""),
                schedule.get("result_date", ""),
                schedule.get("exam_type", ""),
            ))

            saved_count += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return saved_count


# =========================================================
# 5. 저장된 시험 일정 조회
# =========================================================

def get_saved_schedules(keyword=""):
    """
    저장된 시험 일정 중 오늘 이후 일정을 조회한다.
    """
    today = date.today().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if keyword:
            cursor.execute("""
                SELECT *
                FROM exam_schedules
                WHERE exam_date >= ?
                  AND exam_name LIKE ?
                ORDER BY exam_date, exam_time
            """, (
                today,
                f"%{keyword}%"
            ))
        else:
            cursor.execute("""
                SELECT *
                FROM exam_schedules
                WHERE exam_date >= ?
                ORDER BY exam_date, exam_time
            """, (today,))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_schedule_count():
    """
    저장된 시험 일정 개수 조회
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM exam_schedules
        """)

        row = cursor.fetchone()
        return row["count"]

    finally:
        conn.close()


# =========================================================
# 6. 로드맵 과제 ID 생성
# =========================================================

def make_roadmap_task_id(
    task,
    user_id="demo-user"
):
    """
    로드맵 과제 고유 ID 생성
    """
    raw = "|".join([
        user_id,
        str(task.get("exam_name", "")),
        str(task.get("exam_date", "")),
        str(task.get("task_date", "")),
        str(task.get("task_type", "")),
        str(task.get("title", "")),
    ])

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# =========================================================
# 7. 로드맵 과제 저장
# =========================================================

def save_roadmap_tasks(
    tasks,
    user_id="demo-user"
):
    """
    로드맵 과제를 저장한다.
    기존 과제의 진행 상태는 유지한다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    saved_count = 0

    try:
        for task in tasks:
            task_id = make_roadmap_task_id(
                task,
                user_id
            )

            cursor.execute("""
                INSERT INTO roadmap_tasks (
                    task_id,
                    user_id,
                    exam_name,
                    exam_date,
                    task_date,
                    task_type,
                    title,
                    description,
                    is_notification,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(task_id) DO UPDATE SET
                    exam_name = excluded.exam_name,
                    exam_date = excluded.exam_date,
                    task_date = excluded.task_date,
                    task_type = excluded.task_type,
                    title = excluded.title,
                    description = excluded.description,
                    is_notification = excluded.is_notification,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                task_id,
                user_id,
                task.get("exam_name", ""),
                task.get("exam_date", ""),
                task.get("task_date", ""),
                task.get("task_type", ""),
                task.get("title", ""),
                task.get("description", ""),
                int(bool(task.get("is_notification", False))),
                task.get("status", "pending"),
            ))

            saved_count += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return saved_count


# =========================================================
# 8. 로드맵 과제 조회
# =========================================================

def get_roadmap_tasks(
    user_id="demo-user",
    keyword=""
):
    """
    저장된 로드맵 과제를 조회한다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if keyword:
            cursor.execute("""
                SELECT *
                FROM roadmap_tasks
                WHERE user_id = ?
                  AND exam_name LIKE ?
                ORDER BY task_date, exam_name
            """, (
                user_id,
                f"%{keyword}%"
            ))
        else:
            cursor.execute("""
                SELECT *
                FROM roadmap_tasks
                WHERE user_id = ?
                ORDER BY task_date, exam_name
            """, (user_id,))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# =========================================================
# 9. 로드맵 과제 상태 변경
# =========================================================

def update_roadmap_task_status(
    task_id,
    status,
    user_id="demo-user"
):
    """
    과제 진행 상태를 변경한다.
    """
    allowed_statuses = [
        "pending",
        "in_progress",
        "completed"
    ]

    if status not in allowed_statuses:
        raise ValueError(
            "허용되지 않는 상태입니다."
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE roadmap_tasks
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
              AND user_id = ?
        """, (
            status,
            task_id,
            user_id
        ))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# =========================================================
# 10. 자격증 선택 저장
# =========================================================

def save_user_certification(
    user_id,
    cert_id,
    cert_name
):
    """
    사용자가 선택한 자격증을 저장한다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO user_certifications (
                user_id,
                cert_id,
                cert_name
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            cert_id,
            cert_name
        ))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# =========================================================
# 11. 사용자 선택 자격증 조회
# =========================================================

def get_user_certifications(user_id):
    """
    사용자가 선택한 자격증 목록을 조회한다.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                user_id,
                cert_id,
                cert_name,
                selected_at
            FROM user_certifications
            WHERE user_id = ?
            ORDER BY selected_at DESC
        """, (user_id,))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# =========================================================
# 12. 사용자 선택 자격증 삭제
# =========================================================


def delete_user_certification(
    user_id,
    cert_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM user_certifications
        WHERE user_id = ?
        AND cert_id = ?
        """,
        (str(user_id), str(cert_id))
    )

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


def create_user(
    username,
    password_hash,
    display_name
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (
                username,
                password_hash,
                display_name
            )
            VALUES (?, ?, ?)
        """, (
            username,
            password_hash,
            display_name
        ))

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                username,
                display_name,
                created_at
            FROM users
            WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:
        conn.close()
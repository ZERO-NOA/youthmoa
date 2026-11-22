# Backend

백석대 첨단IT학부 커리어 내비게이션의 백엔드입니다.
K-DATA 시험 일정 API에서 자격증 시험 일정을 가져와 SQLite에 저장하고, 사용자별 로드맵 할 일(task)을 관리합니다.

## 기술 스택

| 구분 | 사용 기술 |
|---|---|
| 언어 | Python 3.10+ |
| 웹 프레임워크 | FastAPI, Uvicorn |
| 외부 API 호출 | requests |
| 환경변수 | python-dotenv |
| DB | SQLite (`roadmap.db`) |

## 폴더 구조

```
backend/
├─ app/
│  └─ services/
│     └─ kdata_client.py   # K-DATA 시험 일정 API 호출 (get_kdata_schedule_data)
├─ test_kdata.py           # K-DATA 연동 확인 스크립트
├─ roadmap.db              # SQLite DB (git 제외)
├─ requirements.txt
├─ .env                    # 환경변수 (git 제외)
└─ .gitignore
```

> TODO: `app/main.py`, 라우터 등 나머지 구조는 코드 확인 후 채워 주세요.

## 실행 방법

### 1. 가상환경 생성 및 활성화

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux / Git Bash
source .venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`backend/` 폴더에 `.env` 파일을 만들고 K-DATA(공공데이터포털) 인증키를 넣습니다.
`.env`는 `.gitignore`에 등록되어 있으므로 커밋되지 않습니다.

```
# TODO: kdata_client.py에서 실제로 읽는 변수 이름으로 교체
KDATA_SERVICE_KEY=발급받은_인증키
```

### 4. 서버 실행

```bash
# TODO: 실제 진입점에 맞게 확인 (app/main.py 기준 예시)
uvicorn app.main:app --reload --port 8000
```

실행 후 접속 주소:

- API 서버: `http://localhost:8000`
- 자동 생성 API 문서(Swagger): `http://localhost:8000/docs`
- 대체 문서(ReDoc): `http://localhost:8000/redoc`

## 데이터베이스

`roadmap.db`는 `*.db` 규칙 때문에 Git에 올라가지 않습니다.
처음 받는 팀원은 DB가 없으므로, 서버 또는 초기화 코드가 테이블을 생성하는지 확인하세요. (TODO: DB 초기화 방법 명시)

### 테이블

**exam_schedules**: 자격증 시험 일정

| 컬럼 | 설명 |
|---|---|
| `id` | PK (자동 증가) |
| `schedule_key` | 일정 고유 키 (UNIQUE, 중복 저장 방지) |
| `source` | 데이터 출처 (예: `K-DATA`) |
| `exam_name` | 시험명 (예: `빅데이터분석기사-실기`) |
| `exam_category` | 시험 분류 (예: `일반검정`) |
| `exam_round` | 회차 |
| `exam_date`, `exam_time` | 시험일, 시험 시간 |
| `registration_start`, `registration_end` | 접수 시작일, 접수 마감일 |
| `result_date` | 합격 발표일 |
| `exam_type` | 필기/실기 구분 |
| `created_at`, `updated_at` | 생성/수정 시각 |

**roadmap_tasks**: 사용자별 로드맵 할 일

| 컬럼 | 설명 |
|---|---|
| `task_id` | PK |
| `user_id` | 사용자 |
| `exam_name`, `exam_date` | 연결된 시험 |
| `task_date` | 할 일 날짜 |
| `task_type` | `study`(학습), `exam`(시험), `result`(발표) 등 |
| `title`, `description` | 제목, 설명 |
| `is_notification` | 알림 여부 (0/1) |
| `status` | 진행 상태 (기본값 `pending`) |

**user_certifications**: 사용자가 선택한 자격증 (`user_id` + `cert_id` UNIQUE)

**users**: 사용자 계정 (`username` UNIQUE, `password_hash`, `display_name`)

### DB 내용 확인

```bash
python - << 'PY'
import sqlite3
c = sqlite3.connect("roadmap.db")
for t in ["exam_schedules", "roadmap_tasks", "user_certifications", "users"]:
    print(t, c.execute(f"select count(*) from {t}").fetchone()[0])
PY
```

## 기능별 테스트 방법

### 1) K-DATA API 연동 테스트

`app` 패키지를 import 하므로 반드시 **`backend/` 폴더에서** 실행합니다.

```bash
python test_kdata.py
```

출력은 세 부분으로 나뉩니다.

| 출력 구간 | 확인할 내용 |
|---|---|
| `K-DATA 원본 확인` | 전체 데이터 개수, 실제 필드명, 첫 번째 데이터 |
| `ADsP 검색` | 시험명에 `ADSP` 또는 `데이터분석 준전문가`가 포함된 일정 (최대 10건 출력) |
| `미래 일정 확인` | 오늘 이후의 전체 시험 일정 수, 미래 ADsP 일정, 전체 미래 일정 상세 |

정상 기준:

- 전체 데이터 개수가 0보다 크다.
- 필드명에 `시험명`, `시험일`, `접수시작일`, `접수마감일`, `회차`가 포함되어 있다.
- 미래 일정이 한 건 이상 출력된다.

문제 해결:

| 증상 | 원인과 조치 |
|---|---|
| `ModuleNotFoundError: app` | `backend/` 폴더에서 실행했는지 확인 |
| 전체 데이터 개수 `0` | 인증키 오류, 활용신청 미승인, 호출 한도 초과 가능성. `.env` 확인 |
| 필드명이 위와 다름 | API 응답 형식이 바뀐 것이므로 `kdata_client.py`와 이 스크립트의 키 이름 수정 |
| 미래 일정이 `0` | 공식 일정 미공고 시기일 수 있음 |

### 2) DB 저장 테스트

1. 시험 일정 저장 로직을 실행합니다. (TODO: 저장 함수 또는 엔드포인트 이름)
2. `exam_schedules`의 건수가 늘었는지 확인합니다.

```bash
python -c "import sqlite3; c=sqlite3.connect('roadmap.db'); print(c.execute('select exam_name, exam_date, registration_start, registration_end from exam_schedules order by exam_date').fetchall())"
```

3. 같은 저장 로직을 한 번 더 실행해도 건수가 늘지 않아야 합니다. (`schedule_key` UNIQUE 기준 중복 방지)

### 3) REST API 테스트

서버 실행 후 `http://localhost:8000/docs`에서 각 엔드포인트의 **Try it out** 버튼으로 바로 테스트할 수 있습니다.
curl 예시는 아래 형식을 따릅니다. (TODO: 실제 경로로 교체)

```bash
curl http://localhost:8000/<엔드포인트>
```

확인 항목: 응답 코드 `200`, JSON 구조, 존재하지 않는 값 조회 시 빈 결과 또는 `404`.

## 주의사항

- `.env`, `*.db` 파일은 Git에 커밋하지 않습니다. (`.gitignore`에 등록됨)
- `users` 테이블에는 해시된 비밀번호만 저장합니다. DB 파일을 외부에 공유하지 마세요.
- 인증키가 커밋 기록에 한 번이라도 올라갔다면 공공데이터포털에서 키를 재발급하세요.


from datetime import date, datetime

from app.services.kdata_client import get_kdata_schedule_data


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    # API 날짜 형식 확인
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


data = get_kdata_schedule_data()

print("========== K-DATA 원본 확인 ==========")
print("전체 데이터 개수:", len(data))

if data:
    print("실제 필드명:", list(data[0].keys()))
    print("첫 번째 데이터:", data[0])

today = date.today()

adsps = []
future_count = 0

for item in data:
    name = str(item.get("시험명", ""))
    exam_date_raw = item.get("시험일")
    exam_date = parse_date(exam_date_raw)

    if exam_date and exam_date >= today:
        future_count += 1

    if (
        "ADSP" in name.upper()
        or "데이터분석 준전문가" in name
    ):
        adsps.append(item)

print("\n========== ADsP 검색 ==========")
print("ADsP 관련 데이터 개수:", len(adsps))

for item in adsps[:10]:
    print(
        "시험명:", item.get("시험명"),
        "| 시험일:", item.get("시험일"),
        "| 접수시작:", item.get("접수시작일"),
        "| 접수마감:", item.get("접수마감일"),
    )

print("\n========== 미래 일정 확인 ==========")
print("오늘 날짜:", today)
print("전체 미래 시험 일정 수:", future_count)

future_adsps = []

for item in adsps:
    exam_date = parse_date(item.get("시험일"))

    if exam_date and exam_date >= today:
        future_adsps.append(item)

print("미래 ADsP 일정 수:", len(future_adsps))

for item in future_adsps:
    print(item)

print("\n========== 전체 미래 일정 상세 ==========")

for item in data:
    exam_date = parse_date(item.get("시험일"))

    if exam_date and exam_date >= today:
        print("시험명:", item.get("시험명"))
        print("시험일:", item.get("시험일"))
        print("접수 시작:", item.get("접수시작일"))
        print("접수 마감:", item.get("접수마감일"))
        print("회차:", item.get("회차"))
        print("-" * 40)
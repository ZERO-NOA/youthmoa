
import requests

from app.core.config import (
    KDATA_API_KEY,
    KDATA_API_URL,
)


def get_kdata_schedule_data():
    """
    한국데이터산업진흥원 데이터 자격검정 시험 정보 조회
    """

    if not KDATA_API_KEY:
        raise ValueError(
            "KDATA_API_KEY가 .env에 설정되지 않았습니다."
        )

    params = {
        "page": 1,
        "perPage": 1000,
        "returnType": "JSON",
        "serviceKey": KDATA_API_KEY,
    }

    response = requests.get(
        KDATA_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    return result.get("data", [])

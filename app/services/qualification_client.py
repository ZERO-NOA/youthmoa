
import requests

from app.core.config import (
    QUALIFICATION_API_KEY,
    QUALIFICATION_API_URL,
)


def get_qualification_list(
    page: int = 1,
    per_page: int = 100,
):
    if not QUALIFICATION_API_KEY:
        raise ValueError(
            "API 인증키가 설정되지 않았습니다."
        )

    params = {
        "page": page,
        "perPage": per_page,
        "returnType": "JSON",
        "serviceKey": QUALIFICATION_API_KEY,
    }

    response = requests.get(
        QUALIFICATION_API_URL,
        params=params,
        timeout=30,
    )

    print("외부 API 상태 코드:", response.status_code)

    response.raise_for_status()

    result = response.json()

    print("외부 API 응답 전체:")
    print(result)

    return result


import os
from pathlib import Path

from dotenv import load_dotenv


# 프로젝트 최상위 폴더의 .env 파일 경로
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

# .env 파일 불러오기
load_dotenv(dotenv_path=ENV_PATH)


# 기존 국가자격 API 설정
QUALIFICATION_API_KEY = os.getenv(
    "QUALIFICATION_API_KEY"
)

QUALIFICATION_API_URL = (
    "https://api.odcloud.kr/api/15082998/v1/"
    "uddi:b6f6b8a3-05b8-4a06-bc59-e81477c9f0fb"
)


# K-DATA API 설정
KDATA_API_KEY = os.getenv(
    "KDATA_API_KEY"
)

KDATA_API_URL = (
    "https://api.odcloud.kr/api/15062838/v1/"
    "uddi:203e0beb-5aa5-448d-a167-c6e3f0cf2f4d"
)

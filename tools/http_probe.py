import requests
from .. import settings

TARGET = settings.TARGET_DOMAIN

def head_ok(url: str = TARGET) -> bool:
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def get_login_page_snippet() -> tuple[int, str]:
    try:
        r = requests.get(TARGET, timeout=15)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return 0, str(e)
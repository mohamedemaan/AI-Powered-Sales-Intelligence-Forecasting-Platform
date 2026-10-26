import httpx
import time

try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/analytics/overview")
    print("STATUS:", r.status_code)
    print("BODY:", r.text)
except Exception as e:
    print("ERROR:", e)

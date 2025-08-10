import os
os.environ.setdefault("NFL_API_BASE","https://example.com")
from app import app
from fastapi.testclient import TestClient
client = TestClient(app)

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True

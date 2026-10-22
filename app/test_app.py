import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def create_link(client, url="https://www.github.com"):
    resp = client.post("/shorten", json={"url": url})
    return resp.get_json()["code"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_shorten_creates_link(client):
    resp = client.post("/shorten", json={"url": "https://www.github.com"})
    assert resp.status_code == 201
    assert len(resp.get_json()["code"]) == 6


def test_shorten_rejects_invalid_url(client):
    resp = client.post("/shorten", json={"url": "pas-un-lien"})
    assert resp.status_code == 400


def test_redirect(client):
    code = create_link(client, "https://www.example.com")
    resp = client.get(f"/{code}")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://www.example.com"


def test_unknown_code_returns_404(client):
    resp = client.get("/zzzzzzzzzz")
    assert resp.status_code == 404


def test_cache_miss_then_hit(client):
    code = create_link(client)
    first = client.get(f"/{code}")
    second = client.get(f"/{code}")
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"


def test_stats_count_clicks(client):
    code = create_link(client)
    for _ in range(3):
        client.get(f"/{code}")
    resp = client.get(f"/stats/{code}")
    assert resp.get_json()["clicks"] == 3

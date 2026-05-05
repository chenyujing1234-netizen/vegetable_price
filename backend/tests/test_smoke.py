"""冒烟测试：FastAPI 路由可以挂载、Schema 不互相打架"""

from fastapi.testclient import TestClient


def test_app_imports():
    from app.main import app

    assert app.title == "蔬菜价格预测 SaaS API"


def test_root_endpoint():
    from app.main import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "Vegetable Price Intelligence API"


def test_health_endpoint():
    from app.main import app

    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}

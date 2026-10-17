import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import get_settings
from app.db.base import get_session
from app.main import app


def _broken_session(error):
    def override():
        raise error
        yield  # pragma: no cover  (makes this a generator like the real dependency)

    return override


@pytest.fixture()
def origin():
    return get_settings().frontend_origin


@pytest.mark.parametrize("error, expected", [
    (OperationalError("SELECT 1", {}, Exception("secret-host-detail")), "database is unavailable"),
    (ProgrammingError("SELECT 1", {}, Exception("secret-table-detail")), "alembic upgrade head"),
])
def test_database_errors_become_clean_503s_with_cors(error, expected, origin):
    app.dependency_overrides[get_session] = _broken_session(error)
    try:
        response = TestClient(app).get("/api/incidents", headers={"Origin": origin})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert expected in response.json()["detail"]
    # CORS header present, so the browser can read the real message instead of "failed to fetch"
    assert response.headers["access-control-allow-origin"] == origin
    # nothing internal leaks
    assert "secret" not in response.text and "Traceback" not in response.text

import pytest

from app.api.routes import network as network_routes
from app.core.config import Settings, get_settings
from app.main import app
from app.portaldot.rpc import JsonRpcClient
from app.services import network as network_service
from tests.mock_node import MockChain, start


@pytest.fixture(autouse=True)
def fresh_cache():
    network_service.reset_cache()
    yield
    network_service.reset_cache()


@pytest.fixture()
def use_node(client, monkeypatch):
    """Points the API at a fake node. min_refresh_seconds=0 lets tests take several snapshots."""
    stops = []

    def attach(min_refresh=0.0, **kwargs):
        chain = MockChain(**kwargs)
        url, stop = start(chain)
        stops.append(stop)
        monkeypatch.setattr(network_routes, "get_settings", lambda: Settings(network_min_refresh_seconds=min_refresh))
        app.dependency_overrides[network_routes.get_rpc_client] = lambda: JsonRpcClient(url, timeout=3)
        return chain

    yield attach
    for stop in stops:
        stop()


def test_latest_is_404_before_any_snapshot(client):
    assert client.get("/api/network/latest").status_code == 404


def test_refresh_returns_a_live_healthy_snapshot(client, use_node):
    use_node()
    body = client.post("/api/network/refresh").json()
    assert body["snapshot"]["data_origin"] == "live"
    assert body["snapshot"]["distinct_authors"] == 2 and body["snapshot"]["finality_lag"] == 3
    assert body["findings"] == [] and body["risk_score"] == 0 and body["level"] == "low"
    assert body["cached"] is False and "derived" in body["note"]


def test_latest_matches_the_stored_snapshot(client, use_node):
    use_node()
    refreshed = client.post("/api/network/refresh").json()
    latest = client.get("/api/network/latest").json()
    assert latest["snapshot"]["best_block"] == refreshed["snapshot"]["best_block"]
    assert latest["cached"] is True


def test_refresh_is_rate_limited_to_protect_the_public_node(client, use_node):
    chain = use_node(min_refresh=60)
    first = client.post("/api/network/refresh").json()
    requests_after_first = chain.http_requests
    second = client.post("/api/network/refresh").json()
    assert first["cached"] is False and second["cached"] is True
    assert chain.http_requests == requests_after_first          # no new node traffic


def test_history_lists_snapshots_oldest_first(client, use_node):
    use_node()
    for _ in range(3):
        client.post("/api/network/refresh")
    points = client.get("/api/network/history?limit=2").json()
    assert len(points) == 2
    assert points[0]["taken_at"] <= points[1]["taken_at"]
    assert client.get("/api/network/history?limit=0").status_code == 422


def test_a_degraded_chain_raises_findings_and_risk(client, use_node):
    use_node(finalized=960, gaps=tuple(range(950, 1000, 2)))      # finality 40 behind, many empty slots
    body = client.post("/api/network/refresh").json()
    found = {f["rule_id"] for f in body["findings"]}
    assert {"NH-001", "NH-002"} <= found
    assert body["risk_score"] >= 40


def test_a_silent_validator_is_detected_across_snapshots(client, use_node):
    chain = use_node(authors=(0, 1))
    client.post("/api/network/refresh")                           # baseline: both authors active
    chain.authors = (0,)                                          # author 1 goes quiet
    chain.best += 60
    chain.finalized += 60
    network_service.reset_cache()
    body = client.post("/api/network/refresh").json()
    assert "NH-004" in {f["rule_id"] for f in body["findings"]}


def test_an_unreachable_node_gives_a_clean_503_with_cors(client, monkeypatch):
    monkeypatch.setattr(network_routes, "get_settings", lambda: Settings(network_min_refresh_seconds=0))
    app.dependency_overrides[network_routes.get_rpc_client] = lambda: JsonRpcClient("http://127.0.0.1:9", timeout=1)
    origin = get_settings().frontend_origin
    response = client.post("/api/network/refresh", headers={"Origin": origin})
    assert response.status_code == 503
    assert "could not be reached" in response.json()["detail"]
    assert response.headers["access-control-allow-origin"] == origin
    assert "Traceback" not in response.text and "127.0.0.1" not in response.text


def test_a_refusing_node_is_reported_the_same_way(client, use_node):
    use_node(fail_status=403)
    response = client.post("/api/network/refresh")
    assert response.status_code == 503 and "refused" in response.json()["detail"]


def test_a_node_error_is_a_502(client, use_node):
    use_node(header_error=True)
    response = client.post("/api/network/refresh")
    assert response.status_code == 502 and "error" in response.json()["detail"]

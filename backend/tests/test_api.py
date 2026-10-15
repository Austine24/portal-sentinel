from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_assessments_endpoint_flags_the_injected_burst():
    response = client.get("/api/assessments")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    top = items[0]
    assert top["account"] == "demo-wallet-A"
    assert top["data_origin"] == "simulated"
    assert top["risk_score"] >= 40
    assert abs(sum(f["weight"] for f in top["factors"]) - 100) < 0.5


def test_every_assessment_is_labelled_simulated():
    assert all(a["data_origin"] == "simulated" for a in client.get("/api/assessments").json())

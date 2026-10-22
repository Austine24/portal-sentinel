def test_sync_then_list_and_get(client):
    created = client.post("/api/incidents/sync").json()
    assert created["data_origin"] == "simulated"
    assert created["created"] >= 1

    items = client.get("/api/incidents").json()
    assert items and all(i["data_origin"] == "simulated" for i in items)
    first = items[0]
    assert first["public_id"].startswith("INC-")
    assert first["evidence"] == {"prepared": False, "hash": None, "anchored": False, "tx_hash": None, "block": None, "contract": None}

    detail = client.get(f"/api/incidents/{first['id']}").json()
    assert detail["id"] == first["id"]
    assert detail["events"] and detail["factors"]


def test_second_sync_creates_nothing_new(client):
    client.post("/api/incidents/sync")
    again = client.post("/api/incidents/sync").json()
    assert again["created"] == 0


def test_status_flow_over_http(client):
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]

    ok = client.patch(f"/api/incidents/{incident_id}/status", json={"status": "investigating"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "investigating"
    assert "confirmed" in ok.json()["allowed_next"]

    bad = client.patch(f"/api/incidents/{incident_id}/status", json={"status": "resolved"})
    assert bad.status_code == 409


def test_unknown_incident_is_404(client):
    assert client.get("/api/incidents/9999").status_code == 404
    assert client.patch("/api/incidents/9999/status", json={"status": "open"}).status_code == 404


def test_invalid_status_value_is_rejected_with_422(client):
    client.post("/api/incidents/sync")
    incident_id = client.get("/api/incidents").json()[0]["id"]
    assert client.patch(f"/api/incidents/{incident_id}/status", json={"status": "hacked"}).status_code == 422


def test_filter_by_status(client):
    client.post("/api/incidents/sync")
    assert client.get("/api/incidents?status=open").json()
    assert client.get("/api/incidents?status=resolved").json() == []

"""Offline HTTP regressions for site management route dispatch."""

import pytest
from fastapi.testclient import TestClient

from api import server


@pytest.fixture
def site_client(monkeypatch):
    stored = {"_all_sites": {"custom": {"name": "Custom"}}}
    defaults = {"example": {"name": "Example", "baseUrl": "https://example.com"}}
    monkeypatch.setattr(server, "sites_dict", stored)
    monkeypatch.setattr(server, "load_sites_from_file", lambda: defaults.copy())
    monkeypatch.setattr(server, "ACCESS_KEY", None)
    with TestClient(server.web_app) as client:
        yield client, stored, defaults


@pytest.mark.parametrize("path", ["/sites/reset", "/api/sites/reset"])
def test_reset_restores_file_sites_without_request_body(site_client, path):
    client, stored, defaults = site_client
    response = client.post(path)
    assert response.status_code == 200
    assert response.json()["success"] is True
    if path == "/sites/reset":
        assert response.json()["count"] == len(defaults)
    else:
        assert "Loaded 1 sites" in response.json()["stdout"]
    assert stored["_all_sites"] == defaults
    assert "reset" not in stored["_all_sites"]


def test_add_site_still_dispatches_to_dynamic_route(site_client):
    client, stored, _ = site_client
    response = client.post(
        "/sites/new-site", json={"name": "New", "baseUrl": "https://new.example"}
    )
    assert response.status_code == 200
    assert response.json()["site_id"] == "new-site"
    assert stored["_all_sites"]["new-site"]["name"] == "New"
    assert "custom" in stored["_all_sites"]

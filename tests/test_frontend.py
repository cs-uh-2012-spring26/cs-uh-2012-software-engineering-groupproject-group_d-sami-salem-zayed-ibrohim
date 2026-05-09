from http import HTTPStatus


def test_frontend_route_serves_gui(client):
    resp = client.get("/frontend")

    assert resp.status_code == HTTPStatus.OK
    assert b"Fitness Classes" in resp.data
    assert b"recurrence_frequency" in resp.data


def test_frontend_asset_route_serves_javascript(client):
    resp = client.get("/frontend/app.js")

    assert resp.status_code == HTTPStatus.OK
    assert b"/auth/login" in resp.data
    assert b"recurrence" in resp.data

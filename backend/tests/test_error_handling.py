def test_validation_errors_use_standard_error_shape(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["message"] == "Request validation failed."
    assert body["detail"] == "Request validation failed."
    assert isinstance(body["details"], list)


def test_request_id_headers_are_present(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.headers["x-process-time-ms"]

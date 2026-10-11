"""
Automated tests for PDF certificate generation, download, frontend serving, and security protections.
"""

from fastapi.testclient import TestClient


def test_generate_and_download_certificate(client: TestClient):
    """
    Test generating a certificate and successfully downloading the PDF document.
    Verifies HTTP 200, application/pdf content type, and PDF signature bytes.
    """
    payload = {
        "event_name": "FastAPI Masterclass",
        "organization_name": "Python Academy",
        "certificate_title": "Certificate of Excellence",
        "issue_date": "2026-10-11",
        "recipients": [
            {
                "name": "Alex Taylor",
                "email": "alex.taylor@example.com",
                "certificate_text": "Completed advanced API design."
            }
        ]
    }
    create_res = client.post("/api/jobs/", json=payload)
    assert create_res.status_code == 201

    job_data = create_res.json()
    assert job_data["status"] == "COMPLETED"
    certificate_id = job_data["recipients"][0]["certificate_id"]
    assert certificate_id is not None

    download_res = client.get(f"/api/certificates/{certificate_id}/")
    assert download_res.status_code == 200
    assert "application/pdf" in download_res.headers["content-type"]
    assert "Alex_Taylor" in download_res.headers.get("content-disposition", "")

    content = download_res.content
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000


def test_download_nonexistent_certificate_returns_404(client: TestClient):
    """
    Test that attempting to download a non-existent certificate returns HTTP 404.
    """
    response = client.get("/api/certificates/nonexistent-cert-uuid/")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_path_traversal_protection(client: TestClient):
    """
    Test that malicious paths attempting directory traversal are safely rejected with 404.
    """
    malicious_ids = [
        "../../etc/passwd",
        "..%2F..%2Fwindows%2Fsystem32",
        "....//....//boot.ini",
    ]
    for bad_id in malicious_ids:
        response = client.get(f"/api/certificates/{bad_id}/")
        assert response.status_code in (404, 422)


def test_health_check_endpoint(client: TestClient):
    """
    Test the health check endpoint returns 200 and healthy status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_root_serves_frontend_html(client: TestClient):
    """
    Test that GET / returns the minimal frontend studio HTML.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Bulk Certificate Studio" in response.text

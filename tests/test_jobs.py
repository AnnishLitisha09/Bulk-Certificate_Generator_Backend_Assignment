"""
Automated tests for bulk job creation, status retrieval, and recipient queries.
"""

from fastapi.testclient import TestClient


def test_create_bulk_job_success(client: TestClient):
    """
    Test creating a bulk certificate generation job with valid recipients.
    Verifies HTTP 201 Created status, completed job status, and accurate counts.
    """
    payload = {
        "event_name": "Python Programming Workshop",
        "organization_name": "ABC College",
        "certificate_title": "Certificate of Participation",
        "issue_date": "2026-10-11",
        "recipients": [
            {
                "name": "Annish Litisha",
                "email": "litisha@example.com",
                "certificate_text": "For successfully participating in the workshop."
            },
            {
                "name": "Liti",
                "email": "liti@example.com",
                "certificate_text": "For successfully completing the workshop."
            }
        ]
    }

    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["event_name"] == "Python Programming Workshop"
    assert data["organization_name"] == "ABC College"
    assert data["certificate_title"] == "Certificate of Participation"
    assert data["issue_date"] == "2026-10-11"
    assert data["status"] == "COMPLETED"
    assert data["total_recipients"] == 2
    assert data["successful_count"] == 2
    assert data["failed_count"] == 0
    assert data["pending_count"] == 0
    assert data["progress_percentage"] == 100.0
    assert data["completed_at"] is not None

    # Check recipient items
    recipients = data["recipients"]
    assert len(recipients) == 2
    for rec in recipients:
        assert rec["status"] == "SUCCESS"
        assert rec["error_message"] is None
        assert rec["certificate_id"] is not None
        assert rec["download_url"] is not None
        assert f"/api/certificates/{rec['certificate_id']}/" in rec["download_url"]


def test_get_job_status(client: TestClient):
    """
    Test retrieving job status, counts, and recipient details via GET /api/jobs/{job_id}/.
    """
    # 1. Create a job first
    payload = {
        "event_name": "Cloud Computing Summit",
        "organization_name": "Tech Corp",
        "certificate_title": "Certificate of Attendance",
        "issue_date": "2026-10-12",
        "recipients": [
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "certificate_text": "Attended all sessions."
            }
        ]
    }
    create_res = client.post("/api/jobs/", json=payload)
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    # 2. Query status
    status_res = client.get(f"/api/jobs/{job_id}/")
    assert status_res.status_code == 200

    data = status_res.json()
    assert data["id"] == job_id
    assert data["event_name"] == "Cloud Computing Summit"
    assert data["status"] == "COMPLETED"
    assert data["total_recipients"] == 1
    assert data["successful_count"] == 1
    assert data["failed_count"] == 0
    assert data["progress_percentage"] == 100.0
    assert len(data["recipients"]) == 1


def test_get_nonexistent_job_returns_404(client: TestClient):
    """
    Test that requesting an unknown job ID returns HTTP 404 with meaningful error.
    """
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_list_job_recipients_pagination(client: TestClient):
    """
    Test listing recipients for a job with pagination support.
    """
    payload = {
        "event_name": "Web Development Bootcamp",
        "organization_name": "Dev Academy",
        "certificate_title": "Certificate of Completion",
        "issue_date": "2026-10-15",
        "recipients": [
            {"name": f"Student {i}", "email": f"student{i}@example.com"}
            for i in range(1, 6)
        ]
    }
    create_res = client.post("/api/jobs/", json=payload)
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    # Request page 1 with page_size=2
    res_p1 = client.get(f"/api/jobs/{job_id}/recipients/?page=1&page_size=2")
    assert res_p1.status_code == 200
    p1_data = res_p1.json()
    assert p1_data["total"] == 5
    assert p1_data["page"] == 1
    assert p1_data["page_size"] == 2
    assert p1_data["total_pages"] == 3
    assert len(p1_data["items"]) == 2

    # Request page 3 with page_size=2
    res_p3 = client.get(f"/api/jobs/{job_id}/recipients/?page=3&page_size=2")
    assert res_p3.status_code == 200
    p3_data = res_p3.json()
    assert len(p3_data["items"]) == 1
    assert p3_data["items"][0]["name"] == "Student 5"


def test_list_recipients_nonexistent_job_returns_404(client: TestClient):
    """
    Test listing recipients for a nonexistent job ID returns HTTP 404.
    """
    response = client.get("/api/jobs/nonexistent-uuid/recipients/")
    assert response.status_code == 404

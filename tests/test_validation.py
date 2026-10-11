"""
Automated tests for request-level validation, batch limits, and recipient-level isolation.
"""

from fastapi.testclient import TestClient


def test_reject_empty_recipient_list(client: TestClient):
    """
    Test that a request with an empty recipients list is rejected at the HTTP boundary.
    """
    payload = {
        "event_name": "Python Workshop",
        "organization_name": "ABC College",
        "certificate_title": "Certificate of Participation",
        "issue_date": "2026-10-11",
        "recipients": []
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("recipients" in str(err) for err in data.get("errors", []))


def test_reject_missing_required_fields(client: TestClient):
    """
    Test that missing required request-level fields are rejected with HTTP 422.
    """
    # Missing event_name
    payload_no_event = {
        "organization_name": "ABC College",
        "certificate_title": "Certificate of Participation",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "Annish", "email": "annish@example.com"}]
    }
    res = client.post("/api/jobs/", json=payload_no_event)
    assert res.status_code == 422

    # Blank organization_name
    payload_blank_org = {
        "event_name": "Python Workshop",
        "organization_name": "   ",
        "certificate_title": "Certificate of Participation",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "Annish", "email": "annish@example.com"}]
    }
    res = client.post("/api/jobs/", json=payload_blank_org)
    assert res.status_code == 422


def test_reject_excessive_batch_size(client: TestClient):
    """
    Test that a batch exceeding the maximum batch limit of 500 recipients is rejected.
    """
    recipients = [
        {"name": f"Recipient {i}", "email": f"rec{i}@example.com"}
        for i in range(501)
    ]
    payload = {
        "event_name": "Giant Conference",
        "organization_name": "Global Org",
        "certificate_title": "Certificate of Attendance",
        "issue_date": "2026-10-11",
        "recipients": recipients
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422


def test_recipient_level_errors_do_not_block_valid_recipients(client: TestClient):
    """
    Verify the recipient-level isolation policy:
    A batch containing invalid recipient data (empty name, malformed email)
    processes valid recipients successfully while recording detailed errors for failed ones.
    The job completes with COMPLETED_WITH_ERRORS status.
    """
    payload = {
        "event_name": "Data Science Bootcamp",
        "organization_name": "AI Institute",
        "certificate_title": "Certificate of Excellence",
        "issue_date": "2026-10-11",
        "recipients": [
            {
                "name": "Valid Recipient One",
                "email": "valid1@example.com",
                "certificate_text": "Completed top projects."
            },
            {
                "name": "   ",  # Blank name
                "email": "emptyname@example.com",
                "certificate_text": "Should fail due to blank name."
            },
            {
                "name": "Invalid Email Person",
                "email": "not-an-email-at-all",  # Malformed email
                "certificate_text": "Should fail due to invalid email."
            },
            {
                "name": "Valid Recipient Two",
                "email": "valid2@example.com",
                "certificate_text": "Completed all labs."
            }
        ]
    }

    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["total_recipients"] == 4
    assert data["successful_count"] == 2
    assert data["failed_count"] == 2
    assert data["pending_count"] == 0
    assert data["progress_percentage"] == 100.0

    recipients = {r["name"]: r for r in data["recipients"]}

    # Valid recipients
    rec1 = recipients["Valid Recipient One"]
    assert rec1["status"] == "SUCCESS"
    assert rec1["certificate_id"] is not None
    assert rec1["download_url"] is not None
    assert rec1["error_message"] is None

    rec2 = recipients["Valid Recipient Two"]
    assert rec2["status"] == "SUCCESS"
    assert rec2["certificate_id"] is not None
    assert rec2["download_url"] is not None
    assert rec2["error_message"] is None

    # Failed recipients
    rec_blank_name = recipients[""]
    assert rec_blank_name["status"] == "FAILED"
    assert rec_blank_name["certificate_id"] is None
    assert rec_blank_name["download_url"] is None
    assert "name cannot be empty" in rec_blank_name["error_message"].lower()

    rec_bad_email = recipients["Invalid Email Person"]
    assert rec_bad_email["status"] == "FAILED"
    assert rec_bad_email["certificate_id"] is None
    assert rec_bad_email["download_url"] is None
    assert "email" in rec_bad_email["error_message"].lower()

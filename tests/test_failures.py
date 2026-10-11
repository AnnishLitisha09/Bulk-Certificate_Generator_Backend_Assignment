"""
Automated tests simulating individual and complete PDF generation failures.
Verifies failure isolation, transaction rollback safety, and continuing batch execution.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.utils.pdf_generator import generate_certificate_pdf as real_generate_pdf


def test_individual_generation_failure_does_not_halt_subsequent_recipients(client: TestClient):
    """
    Mock the PDF generation service to deterministically fail for the second recipient.
    Verify:
    1. First recipient succeeds.
    2. Second recipient fails and records an error message.
    3. Third recipient STILL SUCCEEDS, proving the batch loop does not abort.
    4. Overall job status is COMPLETED_WITH_ERRORS with accurate counts.
    """
    def mock_generate_pdf(*args, **kwargs):
        recipient_name = kwargs.get("recipient_name") or (args[2] if len(args) > 2 else "")
        if recipient_name == "Failing Recipient":
            raise RuntimeError("Simulated ReportLab internal rendering crash")
        return real_generate_pdf(*args, **kwargs)

    payload = {
        "event_name": "Resilience & Fault Tolerance Workshop",
        "organization_name": "Reliability Engineering Group",
        "certificate_title": "Certificate of Completion",
        "issue_date": "2026-10-11",
        "recipients": [
            {
                "name": "First Recipient",
                "email": "first@example.com",
                "certificate_text": "First recipient should succeed."
            },
            {
                "name": "Failing Recipient",
                "email": "failing@example.com",
                "certificate_text": "This recipient will simulate a PDF crash."
            },
            {
                "name": "Subsequent Recipient",
                "email": "subsequent@example.com",
                "certificate_text": "Subsequent recipient should succeed regardless."
            }
        ]
    }

    with patch("app.services.certificate_service.generate_certificate_pdf", side_effect=mock_generate_pdf):
        response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["total_recipients"] == 3
    assert data["successful_count"] == 2
    assert data["failed_count"] == 1
    assert data["pending_count"] == 0
    assert data["progress_percentage"] == 100.0

    recipients_map = {r["name"]: r for r in data["recipients"]}

    # Recipient 1 should succeed
    r1 = recipients_map["First Recipient"]
    assert r1["status"] == "SUCCESS"
    assert r1["certificate_id"] is not None
    assert r1["download_url"] is not None
    assert r1["error_message"] is None

    # Recipient 2 should fail gracefully with meaningful message
    r2 = recipients_map["Failing Recipient"]
    assert r2["status"] == "FAILED"
    assert r2["certificate_id"] is None
    assert r2["download_url"] is None
    assert "Simulated ReportLab" in r2["error_message"]

    # Recipient 3 should succeed (did not abort after r2 failed!)
    r3 = recipients_map["Subsequent Recipient"]
    assert r3["status"] == "SUCCESS"
    assert r3["certificate_id"] is not None
    assert r3["download_url"] is not None
    assert r3["error_message"] is None


def test_all_recipients_failing_sets_failed_status(client: TestClient):
    """
    Test when all recipients fail PDF generation:
    Job status is marked as FAILED, successful_count is 0, failed_count matches total.
    """
    def mock_fail_all(*args, **kwargs):
        raise RuntimeError("Global PDF generator service unavailable")

    payload = {
        "event_name": "Failure Mode Test",
        "organization_name": "Test Lab",
        "certificate_title": "Certificate of Testing",
        "issue_date": "2026-10-11",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
    }

    with patch("app.services.certificate_service.generate_certificate_pdf", side_effect=mock_fail_all):
        response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "FAILED"
    assert data["total_recipients"] == 2
    assert data["successful_count"] == 0
    assert data["failed_count"] == 2
    assert data["progress_percentage"] == 100.0

    for rec in data["recipients"]:
        assert rec["status"] == "FAILED"
        assert rec["certificate_id"] is None
        assert "Global PDF generator" in rec["error_message"]

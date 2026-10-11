/**
 * Bulk Certificate Generator Studio Client
 * Handles dynamic recipient rows, form submission, job tracking, and PDF download links.
 */

document.addEventListener("DOMContentLoaded", () => {
    const tbody = document.getElementById("recipients-tbody");
    const recipientCountSpan = document.getElementById("recipient-count");
    const jobForm = document.getElementById("job-form");
    const btnAddRecipient = document.getElementById("btn-add-recipient");
    const btnClearRecipients = document.getElementById("btn-clear-recipients");
    const btnLoadSample = document.getElementById("btn-load-sample");
    const btnLoadMixed = document.getElementById("btn-load-mixed");
    const btnSubmit = document.getElementById("btn-submit-job");
    const submitSpinner = document.getElementById("submit-spinner");
    const formErrorBanner = document.getElementById("form-error-banner");

    const resultsPlaceholder = document.getElementById("results-placeholder");
    const jobDisplayArea = document.getElementById("job-display-area");
    const btnLookup = document.getElementById("btn-lookup-job");
    const inputLookup = document.getElementById("job-lookup-id");

    // Initialize issue date to today's local date
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("issue_date").value = today;

    // Add empty recipient row
    function addRecipientRow(name = "", email = "", text = "") {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>
                <input type="text" class="rec-name" placeholder="Recipient Name" value="${name}" required>
            </td>
            <td>
                <input type="text" class="rec-email" placeholder="email@example.com" value="${email}" required>
            </td>
            <td>
                <input type="text" class="rec-text" placeholder="Custom achievement (optional)" value="${text}">
            </td>
            <td style="text-align: center;">
                <button type="button" class="btn-icon-danger btn-remove-row" title="Remove">&times;</button>
            </td>
        `;

        tr.querySelector(".btn-remove-row").addEventListener("click", () => {
            tr.remove();
            updateCount();
        });

        tbody.appendChild(tr);
        updateCount();
    }

    function updateCount() {
        const rows = tbody.querySelectorAll("tr").length;
        recipientCountSpan.textContent = rows;
    }

    function clearAllRecipients() {
        tbody.innerHTML = "";
        updateCount();
    }

    // Load sample batch (includeInvalid = false makes Sarah Jenkins valid)
    function loadSampleBatch(includeInvalid = false) {
        document.getElementById("event_name").value = "Advanced Python & Cloud Architecture Workshop";
        document.getElementById("organization_name").value = "ABC Institute of Technology";
        document.getElementById("certificate_title").value = "Certificate of Completion";

        clearAllRecipients();
        addRecipientRow("Annish Litisha", "litisha@example.com", "For outstanding performance and project completion.");
        addRecipientRow("Liti", "liti@example.com", "For active participation in hands-on backend lab.");
        addRecipientRow("Marcus Sterling", "marcus@example.com", "For completing FastAPI & database architecture modules.");
        
        if (includeInvalid) {
            addRecipientRow("Sarah Jenkins", "invalid-email-address", "Demonstrating individual error isolation (typo email).");
        } else {
            addRecipientRow("Sarah Jenkins", "sarah.jenkins@example.com", "For completing cloud infrastructure security modules.");
        }

        addRecipientRow("David Chen", "david.chen@example.com", "For exceptional algorithmic problem solving.");
    }

    // Event Listeners
    btnAddRecipient.addEventListener("click", () => addRecipientRow());
    btnClearRecipients.addEventListener("click", () => clearAllRecipients());
    btnLoadSample.addEventListener("click", () => loadSampleBatch(false));
    if (btnLoadMixed) {
        btnLoadMixed.addEventListener("click", () => loadSampleBatch(true));
    }

    // Submit Job
    jobForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        formErrorBanner.style.display = "none";
        formErrorBanner.textContent = "";

        const rows = Array.from(tbody.querySelectorAll("tr"));
        if (rows.length === 0) {
            formErrorBanner.textContent = "Please add at least one recipient to generate certificates.";
            formErrorBanner.style.display = "block";
            return;
        }

        const recipients = rows.map((r) => ({
            name: r.querySelector(".rec-name").value.trim(),
            email: r.querySelector(".rec-email").value.trim(),
            certificate_text: r.querySelector(".rec-text").value.trim() || null,
        }));

        const payload = {
            event_name: document.getElementById("event_name").value.trim(),
            organization_name: document.getElementById("organization_name").value.trim(),
            certificate_title: document.getElementById("certificate_title").value.trim(),
            issue_date: document.getElementById("issue_date").value.trim(),
            recipients: recipients,
        };

        // Loading state
        btnSubmit.disabled = true;
        submitSpinner.style.display = "inline-block";

        try {
            const res = await fetch("/api/jobs/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res.json();
            if (!res.ok) {
                let msg = data.detail || "Job creation failed";
                if (data.errors) {
                    msg = data.errors.map((err) => `${err.field}: ${err.message}`).join(", ");
                }
                throw new Error(msg);
            }

            renderJobResults(data);
        } catch (err) {
            formErrorBanner.textContent = err.message || "Failed to process bulk job.";
            formErrorBanner.style.display = "block";
        } finally {
            btnSubmit.disabled = false;
            submitSpinner.style.display = "none";
        }
    });

    // Lookup Job
    btnLookup.addEventListener("click", async () => {
        const jobId = inputLookup.value.trim();
        if (!jobId) return;

        try {
            const res = await fetch(`/api/jobs/${jobId}/`);
            if (!res.ok) {
                alert(`Job ID '${jobId}' not found.`);
                return;
            }
            const data = await res.json();
            renderJobResults(data);
        } catch (err) {
            alert(`Lookup error: ${err.message}`);
        }
    });

    // Render results in UI
    function renderJobResults(job) {
        resultsPlaceholder.style.display = "none";
        jobDisplayArea.style.display = "block";

        document.getElementById("display-job-id").textContent = job.id;
        document.getElementById("display-event-name").textContent = job.event_name;
        document.getElementById("display-issue-date").textContent = job.issue_date;

        // Status badge
        const badge = document.getElementById("display-job-status-badge");
        badge.className = "badge";
        if (job.status === "COMPLETED") {
            badge.classList.add("badge-completed");
            badge.textContent = "COMPLETED";
        } else if (job.status === "COMPLETED_WITH_ERRORS") {
            badge.classList.add("badge-errors");
            badge.textContent = "COMPLETED W/ ERRORS";
        } else if (job.status === "FAILED") {
            badge.classList.add("badge-failed");
            badge.textContent = "FAILED";
        } else {
            badge.classList.add("badge-processing");
            badge.textContent = job.status;
        }

        // Progress bar
        const pct = job.progress_percentage || 0;
        document.getElementById("progress-bar-fill").style.width = `${pct}%`;
        document.getElementById("progress-pct-text").textContent = `${pct}% Complete`;
        document.getElementById("progress-counts-text").textContent = `${job.successful_count + job.failed_count} / ${job.total_recipients} Processed`;

        // Metric boxes
        document.getElementById("metric-total").textContent = job.total_recipients;
        document.getElementById("metric-success").textContent = job.successful_count;
        document.getElementById("metric-failed").textContent = job.failed_count;

        // Bulk download ZIP button & container
        const bulkZipContainer = document.getElementById("bulk-zip-container");
        const btnZip = document.getElementById("btn-download-zip");
        if (bulkZipContainer && btnZip) {
            if (job.successful_count > 0) {
                btnZip.href = `/api/jobs/${job.id}/download/`;
                bulkZipContainer.style.display = "block";
            } else {
                bulkZipContainer.style.display = "none";
            }
        }

        // Results table
        const rTbody = document.getElementById("results-tbody");
        rTbody.innerHTML = "";

        if (job.recipients && job.recipients.length > 0) {
            job.recipients.forEach((rec) => {
                const tr = document.createElement("tr");

                let statusBadge = "";
                let actionBtn = "";

                if (rec.status === "SUCCESS") {
                    statusBadge = `<span class="badge badge-completed">SUCCESS</span>`;
                    actionBtn = `
                        <a href="/api/certificates/${rec.certificate_id}/" target="_blank" class="btn-download">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            View PDF
                        </a>
                    `;
                } else {
                    statusBadge = `<span class="badge badge-failed" title="${rec.error_message || 'Failed'}">FAILED</span>`;
                    actionBtn = `<span style="font-size: 0.75rem; color: #dc2626;">${rec.error_message || 'Error generating'}</span>`;
                }

                tr.innerHTML = `
                    <td><strong>${rec.name || '<em>(Empty)</em>'}</strong></td>
                    <td><code>${rec.email || '<em>(Empty)</em>'}</code></td>
                    <td>${statusBadge}</td>
                    <td>${actionBtn}</td>
                `;
                rTbody.appendChild(tr);
            });
        }
    }

    // Load initial sample rows on first render (all valid by default)
    loadSampleBatch(false);
});

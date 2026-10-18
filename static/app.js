const state = {
    threadId: localStorage.getItem("tripmate_thread_id") || null,
    busy: false,
    loadingTimer: null,
};

const el = {
    form: document.getElementById("travelForm"),
    input: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    messages: document.getElementById("messages"),
    welcomeCard: document.getElementById("welcomeCard"),
    typingCard: document.getElementById("typingCard"),
    newTripBtn: document.getElementById("newTripBtn"),
    clearBtn: document.getElementById("clearBtn"),
    threadDisplay: document.getElementById("threadDisplay"),
    apiStatusDot: document.getElementById("apiStatusDot"),
    apiStatusText: document.getElementById("apiStatusText"),
    toast: document.getElementById("toast"),
    sidebar: document.getElementById("sidebar"),
    mobileMenuBtn: document.getElementById("mobileMenuBtn"),
    stepFlights: document.getElementById("stepFlights"),
    stepHotels: document.getElementById("stepHotels"),
    stepItinerary: document.getElementById("stepItinerary"),
};

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderMarkdown(value) {
    const text = String(value ?? "");
    if (window.marked && window.DOMPurify) {
        return window.DOMPurify.sanitize(window.marked.parse(text));
    }
    return escapeHtml(text).replaceAll("\n", "<br>");
}

function updateThreadDisplay() {
    if (!state.threadId) {
        el.threadDisplay.textContent = "New";
        return;
    }
    el.threadDisplay.textContent =
        state.threadId.length > 16
            ? `${state.threadId.slice(0, 8)}…${state.threadId.slice(-5)}`
            : state.threadId;
    el.threadDisplay.title = state.threadId;
}

function showToast(message) {
    el.toast.textContent = message;
    el.toast.classList.remove("hidden");
    setTimeout(() => el.toast.classList.add("hidden"), 2500);
}

function hideWelcome() {
    el.welcomeCard.classList.add("hidden");
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: "smooth"
        });
    });
}

function addUserMessage(message) {
    hideWelcome();
    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `<div class="message-card">${escapeHtml(message)}</div>`;
    el.messages.appendChild(row);
    scrollToBottom();
}

function buildDetailPanel(title, icon, content) {
    if (!content || !String(content).trim()) return "";
    return `
        <details class="detail-panel">
            <summary><span>${icon}</span>${escapeHtml(title)}</summary>
            <div class="detail-content">${escapeHtml(content)}</div>
        </details>
    `;
}


function sanitizeFilenamePart(value) {
    return String(value ?? "")
        .trim()
        .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
        .slice(0, 60) || "trip";
}

async function copyItinerary(button, itinerary) {
    const text = String(itinerary ?? "").trim();

    if (!text) {
        showToast("No itinerary is available to copy.");
        return;
    }

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = text;
            textarea.style.position = "fixed";
            textarea.style.left = "-9999px";
            textarea.style.top = "0";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();

            const copied = document.execCommand("copy");
            textarea.remove();

            if (!copied) {
                throw new Error("Clipboard copy failed.");
            }
        }

        const original = button.innerHTML;
        button.innerHTML = '<span class="action-icon">✓</span>Copied';

        setTimeout(() => {
            button.innerHTML = original;
        }, 1500);

        showToast("Itinerary copied to clipboard.");
    } catch (error) {
        console.error(error);
        showToast("Could not copy the itinerary.");
    }
}

function downloadItinerary(itinerary) {
    const text = String(itinerary ?? "").trim();

    if (!text) {
        showToast("No itinerary is available to download.");
        return;
    }

    const firstLine =
        text
            .split(/\r?\n/)
            .map(line => line.replace(/^#+\s*/, "").trim())
            .find(line => line.length > 3)
        || "TripMate";

    const filename =
        `${sanitizeFilenamePart(firstLine)}-itinerary.md`;

    const contents = [
        "# TripMate AI Itinerary",
        "",
        text,
        "",
        "---",
        "",
        "Generated with TripMate AI.",
        "Verify prices, schedules, and availability before booking."
    ].join("\n");

    const blob = new Blob(
        [contents],
        { type: "text/markdown;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);

    showToast("Itinerary downloaded.");
}

function printItinerary(itinerary) {
    const text = String(itinerary ?? "").trim();

    if (!text) {
        showToast("No itinerary is available to print.");
        return;
    }

    const printWindow = window.open("", "_blank");

    if (!printWindow) {
        showToast("Allow pop-ups to print the itinerary.");
        return;
    }

    const itineraryHtml = renderMarkdown(text);

    printWindow.document.open();
    printWindow.document.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TripMate AI Itinerary</title>
            <style>
                @page { margin: 0.65in; }

                * { box-sizing: border-box; }

                body {
                    margin: 0;
                    color: #172033;
                    background: #fff;
                    font-family: Arial, Helvetica, sans-serif;
                    line-height: 1.6;
                }

                .print-header {
                    padding-bottom: 16px;
                    margin-bottom: 24px;
                    border-bottom: 2px solid #dce7ee;
                }

                .brand {
                    margin: 0;
                    color: #0d6f62;
                    font-size: 24px;
                    font-weight: 800;
                }

                .subtitle {
                    margin: 4px 0 0;
                    color: #65758a;
                    font-size: 12px;
                }

                .content { font-size: 13px; }

                h1, h2, h3 {
                    color: #101828;
                    page-break-after: avoid;
                }

                h1 { font-size: 23px; }

                h2 {
                    margin-top: 26px;
                    padding-bottom: 7px;
                    font-size: 18px;
                    border-bottom: 1px solid #dce7ee;
                }

                h3 {
                    margin-top: 20px;
                    font-size: 15px;
                }

                p, li {
                    orphans: 3;
                    widows: 3;
                }

                ul, ol { padding-left: 22px; }

                .print-footer {
                    margin-top: 34px;
                    padding-top: 12px;
                    border-top: 1px solid #dce7ee;
                    color: #7b8797;
                    font-size: 10px;
                }

                @media print {
                    body {
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }
                }
            </style>
        </head>
        <body>
            <header class="print-header">
                <div class="brand">TripMate AI</div>
                <p class="subtitle">Travel itinerary</p>
            </header>

            <main class="content">
                ${itineraryHtml}
            </main>

            <footer class="print-footer">
                Generated with TripMate AI. Verify travel prices,
                schedules, and availability before booking.
            </footer>

            <script>
                window.addEventListener("load", () => {
                    window.print();
                });
            <\/script>
        </body>
        </html>
    `);

    printWindow.document.close();
}

function attachItineraryActions(row, itinerary) {
    const copyBtn = row.querySelector("[data-action='copy-itinerary']");
    const printBtn = row.querySelector("[data-action='print-itinerary']");
    const downloadBtn = row.querySelector("[data-action='download-itinerary']");

    if (copyBtn) {
        copyBtn.addEventListener("click", () => {
            copyItinerary(copyBtn, itinerary);
        });
    }

    if (printBtn) {
        printBtn.addEventListener("click", () => {
            printItinerary(itinerary);
        });
    }

    if (downloadBtn) {
        downloadBtn.addEventListener("click", () => {
            downloadItinerary(itinerary);
        });
    }
}


function addAssistantMessage(data) {
    hideWelcome();

    const row = document.createElement("div");
    row.className = "message-row assistant";

    const details = [
        buildDetailPanel("Flight data", "✈", data.flight_results),
        buildDetailPanel("Hotel research", "🏨", data.hotel_results),
        buildDetailPanel("Itinerary draft", "🗓", data.itinerary),
    ].join("");

    const hasItinerary =
        Boolean(data.itinerary && String(data.itinerary).trim());

    row.innerHTML = `
        <div class="assistant-avatar">✈</div>

        <div class="message-card">
            <div class="message-meta">TripMate AI</div>

            <div class="markdown-body">
                ${renderMarkdown(data.answer || "No response returned.")}
            </div>

            ${
                hasItinerary
                    ? `
                        <div class="itinerary-actions">
                            <button
                                class="itinerary-action-btn"
                                type="button"
                                data-action="copy-itinerary"
                            >
                                <span class="action-icon">⧉</span>
                                Copy itinerary
                            </button>

                            <button
                                class="itinerary-action-btn"
                                type="button"
                                data-action="print-itinerary"
                            >
                                <span class="action-icon">🖨</span>
                                Print itinerary
                            </button>

                            <button
                                class="itinerary-action-btn primary"
                                type="button"
                                data-action="download-itinerary"
                            >
                                <span class="action-icon">↓</span>
                                Download itinerary
                            </button>
                        </div>
                    `
                    : ""
            }

            ${details ? `<div class="details-grid">${details}</div>` : ""}

            ${
                typeof data.llm_calls === "number"
                    ? `<div class="agent-stats">AI model calls: ${data.llm_calls}</div>`
                    : ""
            }
        </div>
    `;

    el.messages.appendChild(row);

    if (hasItinerary) {
        attachItineraryActions(row, data.itinerary);
    }

    scrollToBottom();
}

function addErrorMessage(message) {
    hideWelcome();
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.innerHTML = `
        <div class="assistant-avatar">!</div>
        <div class="message-card">
            <div class="error-card">${escapeHtml(message)}</div>
        </div>
    `;
    el.messages.appendChild(row);
    scrollToBottom();
}

function startLoadingAnimation() {
    const steps = [el.stepFlights, el.stepHotels, el.stepItinerary];
    let current = 0;

    steps.forEach((step, index) => {
        step.classList.toggle("active", index === 0);
    });

    state.loadingTimer = setInterval(() => {
        current = (current + 1) % steps.length;
        steps.forEach((step, index) => {
            step.classList.toggle("active", index === current);
        });
    }, 2200);
}

function stopLoadingAnimation() {
    if (state.loadingTimer) {
        clearInterval(state.loadingTimer);
        state.loadingTimer = null;
    }
}

function setBusy(busy) {
    state.busy = busy;
    el.input.disabled = busy;
    el.sendBtn.disabled = busy;

    if (busy) {
        el.typingCard.classList.remove("hidden");
        startLoadingAnimation();
    } else {
        stopLoadingAnimation();
        el.typingCard.classList.add("hidden");
        el.input.disabled = false;
        el.input.focus();
    }
}

function resizeTextarea() {
    el.input.style.height = "auto";
    el.input.style.height = `${Math.min(el.input.scrollHeight, 180)}px`;
}

async function submitTravelRequest(message) {
    const cleanMessage = String(message ?? "").trim();

    if (!cleanMessage || state.busy) return;

    addUserMessage(cleanMessage);
    el.input.value = "";
    resizeTextarea();
    setBusy(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: cleanMessage,
                thread_id: state.threadId,
            }),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || `Request failed (${response.status}).`);
        }

        if (data.thread_id) {
            state.threadId = data.thread_id;
            localStorage.setItem("tripmate_thread_id", state.threadId);
            updateThreadDisplay();
        }

        addAssistantMessage(data);
    } catch (error) {
        console.error(error);
        addErrorMessage(
            error?.message || "TripMate AI could not complete the request."
        );
    } finally {
        setBusy(false);
    }
}

function resetConversation() {
    if (state.busy) return;

    state.threadId = null;
    localStorage.removeItem("tripmate_thread_id");
    el.messages.innerHTML = "";
    el.welcomeCard.classList.remove("hidden");
    el.input.value = "";
    resizeTextarea();
    updateThreadDisplay();
    showToast("Started a new trip.");
    el.input.focus();
}

async function checkHealth() {
    try {
        const response = await fetch("/health");
        const data = await response.json();

        if (!response.ok || data.status !== "ok") {
            throw new Error("API unavailable");
        }

        el.apiStatusDot.classList.remove("offline");
        el.apiStatusDot.classList.add("online");
        el.apiStatusText.textContent = "API online";
    } catch {
        el.apiStatusDot.classList.remove("online");
        el.apiStatusDot.classList.add("offline");
        el.apiStatusText.textContent = "API unavailable";
    }
}

el.form.addEventListener("submit", (event) => {
    event.preventDefault();
    submitTravelRequest(el.input.value);
});

el.input.addEventListener("input", resizeTextarea);

el.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitTravelRequest(el.input.value);
    }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
        el.input.value = button.dataset.prompt || "";
        resizeTextarea();

        if (window.innerWidth <= 950) {
            el.sidebar.classList.remove("open");
        }

        el.input.focus();
    });
});

el.newTripBtn.addEventListener("click", resetConversation);
el.clearBtn.addEventListener("click", resetConversation);

el.mobileMenuBtn.addEventListener("click", () => {
    el.sidebar.classList.toggle("open");
});

document.addEventListener("click", (event) => {
    if (
        window.innerWidth <= 950 &&
        el.sidebar.classList.contains("open") &&
        !el.sidebar.contains(event.target) &&
        !el.mobileMenuBtn.contains(event.target)
    ) {
        el.sidebar.classList.remove("open");
    }
});

updateThreadDisplay();
resizeTextarea();
checkHealth();
setInterval(checkHealth, 30000);

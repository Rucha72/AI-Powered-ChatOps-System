"""
CLI Test Runner - Opens browser with live progress
Run: python tests/run_tests.py
"""

import sys
import os
import json
import time
import threading
import webbrowser
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = "http://localhost:8000"
test_state = {
    "status": "idle",
    "current_test": "",
    "results": [],
    "total": 23,
    "completed": 0,
    "start_time": None,
    "finished": False
}

# ── HTML Page ─────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChatOps AI — Test Runner</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #1a1f2e; color: #c9d1e0;
    font-family: 'Segoe UI', sans-serif; padding: 30px;
    min-height: 100vh;
  }
  .header {
    text-align: center; margin-bottom: 30px;
    padding: 24px; background: #212840;
    border-radius: 12px; border: 1px solid #2e3a58;
  }
  .header h1 { color: #6b8ef5; font-size: 1.8rem; margin-bottom: 6px; }
  .header p { color: #6a7a9a; font-size: 0.9rem; }
  .header .meta { color: #4a5a7a; font-size: 0.8rem; margin-top: 6px; }

  .progress-section {
    background: #212840; border-radius: 12px;
    border: 1px solid #2e3a58; padding: 20px;
    margin-bottom: 24px;
  }
  .progress-label {
    display: flex; justify-content: space-between;
    margin-bottom: 8px; font-size: 0.9rem;
  }
  .progress-label span { color: #6b8ef5; font-weight: 600; }
  .progress-bar-bg {
    background: #2a3250; border-radius: 8px;
    height: 12px; width: 100%; overflow: hidden;
  }
  .progress-bar-fill {
    background: linear-gradient(90deg, #4f6ef7, #6b8ef5);
    height: 12px; border-radius: 8px;
    transition: width 0.4s ease;
    width: 0%;
  }
  .current-test {
    margin-top: 10px; font-size: 0.85rem;
    color: #8a9abf; min-height: 20px;
  }

  .kpi-row {
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 12px; margin-bottom: 24px;
  }
  .kpi-card {
    background: #212840; border: 1px solid #2e3a58;
    border-radius: 10px; padding: 16px; text-align: center;
  }
  .kpi-number { font-size: 2rem; font-weight: 700; }
  .kpi-label { font-size: 0.72rem; color: #6a7a9a;
               text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

  .category-header {
    font-size: 0.95rem; font-weight: 700; color: #6b8ef5;
    margin: 20px 0 8px 0; padding-bottom: 6px;
    border-bottom: 1px solid #2e3650;
  }

  .test-card {
    border-radius: 8px; padding: 10px 16px;
    margin: 4px 0; display: flex;
    justify-content: space-between; align-items: center;
    transition: all 0.3s ease;
  }
  .test-card-pending {
    background: #1e2130; border: 1px solid #2e3650;
    border-left: 4px solid #3a4460;
  }
  .test-card-running {
    background: #1e2a3a; border: 1px solid #2e4060;
    border-left: 4px solid #6b8ef5;
    animation: pulse 1s infinite;
  }
  .test-card-pass {
    background: #1a3326; border: 1px solid #2a5a3a;
    border-left: 4px solid #4aaa6e;
  }
  .test-card-fail {
    background: #331a1a; border: 1px solid #5a2a2a;
    border-left: 4px solid #e05555;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .test-left { display: flex; align-items: center; gap: 10px; flex: 1; }
  .test-id { font-size: 0.78rem; font-weight: 700;
             color: #6b8ef5; min-width: 50px; }
  .test-name { font-size: 0.88rem; color: #c9d1e0; }
  .test-desc { font-size: 0.75rem; color: #4a5a7a; margin-top: 2px; }
  .test-right { text-align: right; min-width: 80px; }
  .test-time { font-size: 0.78rem; color: #4a5a7a; }
  .test-status { font-size: 1rem; }

  .actual-output {
    font-size: 0.75rem; color: #4a8a5a;
    margin-top: 4px; font-style: italic;
  }
  .actual-output-fail { color: #8a4a4a; }

  .summary-banner {
    background: #1a3326; border: 1px solid #2a5a3a;
    border-radius: 12px; padding: 20px; text-align: center;
    margin-top: 24px; display: none;
  }
  .summary-banner.show { display: block; }
  .summary-banner h2 { color: #4aaa6e; font-size: 1.5rem; margin-bottom: 8px; }
  .summary-banner p { color: #6a9a7a; }

  .btn-download {
    background: #2e4a8a; color: white; border: none;
    padding: 10px 24px; border-radius: 8px; cursor: pointer;
    font-size: 0.9rem; margin-top: 12px;
    font-family: 'Segoe UI', sans-serif;
  }
  .btn-download:hover { background: #4f6ef7; }
</style>
</head>
<body>

<div class="header">
  <h1>🧪 ChatOps AI — Automated Test Runner</h1>
  <p>AI-Powered ChatOps System for DevOps Automation</p>
  <div class="meta">BITS Pilani | MTech Software Engineering | Vaidya Rucha Sandeep | 2024TM93058</div>
</div>

<div class="progress-section">
  <div class="progress-label">
    <span id="progress-text">Waiting to start...</span>
    <span id="progress-pct">0%</span>
  </div>
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" id="progress-fill"></div>
  </div>
  <div class="current-test" id="current-test">Initializing...</div>
</div>

<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-number" id="kpi-total" style="color:#6b8ef5;">23</div>
    <div class="kpi-label">Total Tests</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-number" id="kpi-passed" style="color:#4aaa6e;">0</div>
    <div class="kpi-label">Passed</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-number" id="kpi-failed" style="color:#e05555;">0</div>
    <div class="kpi-label">Failed</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-number" id="kpi-rate" style="color:#4aaa6e;">0%</div>
    <div class="kpi-label">Pass Rate</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-number" id="kpi-time" style="color:#e08830;">0ms</div>
    <div class="kpi-label">Avg Time</div>
  </div>
</div>

<div id="test-list"></div>

<div class="summary-banner" id="summary-banner">
  <h2 id="summary-title">✅ All Tests Passed!</h2>
  <p id="summary-text"></p>
</div>

<script>
const CATEGORIES = [
  { name: "🔌 API Connectivity", ids: ["TC-01","TC-02","TC-03","TC-04","TC-05"] },
  { name: "💬 Intent Detection", ids: ["TC-06","TC-07","TC-08","TC-09","TC-10","TC-11","TC-12","TC-13","TC-14","TC-15"] },
  { name: "🔄 Conversation Context", ids: ["TC-16","TC-17"] },
  { name: "🛡️ Edge Cases", ids: ["TC-18","TC-19","TC-20","TC-21","TC-22","TC-23"] }
];

const TEST_NAMES = {
  "TC-01": "Backend health endpoint",
  "TC-02": "Root endpoint reachable",
  "TC-03": "Chat endpoint reachable",
  "TC-04": "Invalid endpoint returns 404",
  "TC-05": "Chat returns non-empty reply",
  "TC-06": "Greeting intent handled",
  "TC-07": "Service status — all services",
  "TC-08": "Service status — specific service",
  "TC-09": "Incident summary INC-001",
  "TC-10": "Knowledge base search",
  "TC-11": "DevOps restart action",
  "TC-12": "DevOps scale action",
  "TC-13": "DevOps rollback action",
  "TC-14": "RCA from pasted logs",
  "TC-15": "List incidents by service",
  "TC-16": "Context maintained across turns",
  "TC-17": "Multi-turn conversation coherent",
  "TC-18": "Empty message handled gracefully",
  "TC-19": "Very long message handled",
  "TC-20": "Invalid incident ID — friendly message",
  "TC-21": "Unknown service query handled",
  "TC-22": "Missing history field defaults",
  "TC-23": "Response time under 10 seconds"
};

const TEST_DESCS = {
  "TC-01": "GET /health → HTTP 200",
  "TC-02": "GET / → HTTP 200",
  "TC-03": "POST /chat → reply field present",
  "TC-04": "GET /invalid → HTTP 404",
  "TC-05": "Reply is non-empty string",
  "TC-06": "Bot responds to hello",
  "TC-07": "Lists all 9 services with statuses",
  "TC-08": "Returns order-service status",
  "TC-09": "Summarizes payment outage correctly",
  "TC-10": "Finds Redis cache related incidents",
  "TC-11": "Simulates restart for payment-service",
  "TC-12": "Simulates scale to 4 replicas",
  "TC-13": "Simulates rollback for auth-service",
  "TC-14": "Analyzes pasted log content",
  "TC-15": "Lists auth-service incidents",
  "TC-16": "Follow-up uses previous context",
  "TC-17": "Coherent over 4-turn history",
  "TC-18": "No crash on whitespace message",
  "TC-19": "No crash on very long message",
  "TC-20": "INC-999 gives friendly message",
  "TC-21": "Unknown service handled gracefully",
  "TC-22": "Missing history defaults to empty",
  "TC-23": "Response under 10 seconds"
};

// Build initial pending UI
function buildUI() {
  const container = document.getElementById('test-list');
  CATEGORIES.forEach(cat => {
    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = cat.name;
    container.appendChild(header);
    cat.ids.forEach(id => {
      const card = document.createElement('div');
      card.className = 'test-card test-card-pending';
      card.id = `card-${id}`;
      card.innerHTML = `
        <div class="test-left">
          <div>
            <div style="display:flex;gap:8px;align-items:center;">
              <span class="test-id">${id}</span>
              <span class="test-name">${TEST_NAMES[id]}</span>
            </div>
            <div class="test-desc">${TEST_DESCS[id]}</div>
          </div>
        </div>
        <div class="test-right">
          <div class="test-status" id="status-${id}">○</div>
          <div class="test-time" id="time-${id}"></div>
        </div>`;
      container.appendChild(card);
    });
  });
}

// Poll server for updates
function poll() {
  fetch('/state')
    .then(r => r.json())
    .then(data => {
      updateUI(data);
      if (!data.finished) setTimeout(poll, 300);
      else showSummary(data);
    })
    .catch(() => setTimeout(poll, 500));
}

function updateUI(data) {
  const completed = data.completed;
  const total = data.total;
  const pct = total > 0 ? Math.round(completed / total * 100) : 0;

  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-pct').textContent = pct + '%';
  document.getElementById('progress-text').textContent =
    data.finished ? '✅ All tests completed!' : `Running tests... ${completed}/${total}`;
  document.getElementById('current-test').textContent =
    data.current_test ? `▶ Currently running: ${data.current_test}` : '';

  let passed = 0, failed = 0, totalTime = 0;
  data.results.forEach(r => {
    if (r.passed) passed++; else failed++;
    totalTime += r.duration_ms;

    const card = document.getElementById(`card-${r.id}`);
    const statusEl = document.getElementById(`status-${r.id}`);
    const timeEl = document.getElementById(`time-${r.id}`);

    if (card) {
      card.className = `test-card ${r.passed ? 'test-card-pass' : 'test-card-fail'}`;
      const outputDiv = card.querySelector('.actual-output') ||
        (() => { const d = document.createElement('div'); card.querySelector('.test-left div').appendChild(d); return d; })();
      outputDiv.className = `actual-output ${r.passed ? '' : 'actual-output-fail'}`;
      outputDiv.textContent = r.actual ? `→ ${r.actual.substring(0, 80)}` : '';
    }
    if (statusEl) statusEl.textContent = r.passed ? '✅' : '❌';
    if (timeEl) timeEl.textContent = `${r.duration_ms}ms`;
  });

  // Running card pulse
  if (data.current_test) {
    const runCard = document.getElementById(`card-${data.current_test}`);
    if (runCard && !runCard.classList.contains('test-card-pass') &&
        !runCard.classList.contains('test-card-fail')) {
      runCard.className = 'test-card test-card-running';
      document.getElementById(`status-${data.current_test}`).textContent = '⟳';
      runCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  const avgTime = (passed + failed) > 0 ? Math.round(totalTime / (passed + failed)) : 0;
  const rate = total > 0 ? Math.round(passed / total * 100) : 0;

  document.getElementById('kpi-passed').textContent = passed;
  document.getElementById('kpi-failed').textContent = failed;
  document.getElementById('kpi-rate').textContent = rate + '%';
  document.getElementById('kpi-rate').style.color = rate === 100 ? '#4aaa6e' : '#e08830';
  document.getElementById('kpi-time').textContent = avgTime + 'ms';
  document.getElementById('kpi-failed').style.color = failed > 0 ? '#e05555' : '#4aaa6e';
}

function showSummary(data) {
  const passed = data.results.filter(r => r.passed).length;
  const total = data.total;
  const rate = Math.round(passed / total * 100);
  const banner = document.getElementById('summary-banner');
  banner.classList.add('show');
  banner.style.background = rate === 100 ? '#1a3326' : '#2a1a0a';
  banner.style.borderColor = rate === 100 ? '#2a5a3a' : '#5a3a0a';
  document.getElementById('summary-title').textContent =
    rate === 100 ? '✅ All Tests Passed!' : `⚠️ ${passed}/${total} Tests Passed`;
  document.getElementById('summary-title').style.color =
    rate === 100 ? '#4aaa6e' : '#e08830';
  document.getElementById('summary-text').textContent =
    `${passed} passed · ${total - passed} failed · Pass rate: ${rate}% · Run completed at ${new Date().toLocaleTimeString()}`;
}

buildUI();
poll();
</script>
</body>
</html>"""


# ── HTTP Server ───────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == '/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(test_state).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress server logs


# ── Test functions ────────────────────────────────────────────────────────────
def _chat(message, history=None):
    try:
        r = requests.post(f"{BACKEND_URL}/chat",
                          json={"message": message, "history": history or []},
                          timeout=20)
        return r.json().get("reply", "") if r.status_code == 200 else ""
    except Exception:
        return ""


ALL_TESTS = [
    # API Connectivity
    ("TC-01", "🔌 API Connectivity", "Backend health endpoint",
     lambda: (lambda r: {"passed": r.status_code == 200 and r.json().get("status") == "ok",
                         "actual": f"HTTP {r.status_code}"}
              )(requests.get(f"{BACKEND_URL}/health", timeout=5))),

    ("TC-02", "🔌 API Connectivity", "Root endpoint reachable",
     lambda: (lambda r: {"passed": r.status_code == 200, "actual": f"HTTP {r.status_code}"}
              )(requests.get(f"{BACKEND_URL}/", timeout=5))),

    ("TC-03", "🔌 API Connectivity", "Chat endpoint reachable",
     lambda: (lambda r: {"passed": r.status_code == 200 and "reply" in r.json(),
                         "actual": f"HTTP {r.status_code}"}
              )(requests.post(f"{BACKEND_URL}/chat",
                              json={"message": "hello", "history": []}, timeout=15))),

    ("TC-04", "🔌 API Connectivity", "Invalid endpoint returns 404",
     lambda: (lambda r: {"passed": r.status_code == 404, "actual": f"HTTP {r.status_code}"}
              )(requests.get(f"{BACKEND_URL}/invalid", timeout=5))),

    ("TC-05", "🔌 API Connectivity", "Chat returns non-empty reply",
     lambda: (lambda r: {"passed": len(r) > 0, "actual": f"Reply: {len(r)} chars"}
              )(_chat("hello"))),

    # Intent Detection
    ("TC-06", "💬 Intent Detection", "Greeting intent handled",
     lambda: (lambda r: {"passed": len(r) > 10, "actual": r[:80]}
              )(_chat("hello"))),

    ("TC-07", "💬 Intent Detection", "Service status — all services",
     lambda: (lambda r: {"passed": sum(1 for k in ["payment", "auth", "order", "healthy", "degraded"]
                                       if k in r.lower()) >= 3,
                         "actual": f"Keywords found in response"}
              )(_chat("show all service statuses"))),

    ("TC-08", "💬 Intent Detection", "Service status — specific service",
     lambda: (lambda r: {"passed": "order" in r.lower() and
                                   ("degraded" in r.lower() or "healthy" in r.lower()),
                         "actual": r[:80]}
              )(_chat("what is the status of order-service?"))),

    ("TC-09", "💬 Intent Detection", "Incident summary INC-001",
     lambda: (lambda r: {"passed": sum(1 for k in ["payment", "database", "connection", "root", "resolution"]
                                       if k in r.lower()) >= 2,
                         "actual": r[:80]}
              )(_chat("summarize incident INC-001"))),

    ("TC-10", "💬 Intent Detection", "Knowledge base search",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["inc-", "incident", "redis", "similar", "cache"]),
                         "actual": r[:80]}
              )(_chat("find incidents similar to Redis cache failure"))),

    ("TC-11", "💬 Intent Detection", "DevOps restart action",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["restart", "triggered", "payment", "simulated"]),
                         "actual": r[:80]}
              )(_chat("restart payment-service"))),

    ("TC-12", "💬 Intent Detection", "DevOps scale action",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["scale", "replica", "order", "simulated"]),
                         "actual": r[:80]}
              )(_chat("scale order-service to 4 replicas"))),

    ("TC-13", "💬 Intent Detection", "DevOps rollback action",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["rollback", "auth", "version", "simulated"]),
                         "actual": r[:80]}
              )(_chat("rollback auth-service"))),

    ("TC-14", "💬 Intent Detection", "RCA from pasted logs",
     lambda: (lambda r: {"passed": sum(1 for k in ["root cause", "database", "connection",
                                                    "recommend", "timeout"] if k in r.lower()) >= 2,
                         "actual": r[:80]}
              )(_chat("analyze these logs:\n2026-01-01T10:00:00Z ERROR payment-service: DB timeout\n2026-01-01T10:01:00Z ERROR payment-service: Max retries exceeded\n2026-01-01T10:02:00Z WARN postgres-db: pool at 98%"))),

    ("TC-15", "💬 Intent Detection", "List incidents by service",
     lambda: (lambda r: {"passed": "INC-002" in r or "auth" in r.lower(),
                         "actual": r[:80]}
              )(_chat("show all incidents for auth-service"))),

    # Conversation Context
    ("TC-16", "🔄 Conversation Context", "Context maintained across turns",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["order", "replica", "restart", "scale", "degraded", "fix"]),
                         "actual": r[:80]}
              )(_chat("what should I do to fix it?", [
                  {"role": "user", "content": "show me order-service status"},
                  {"role": "assistant", "content": "order-service is degraded with 2/3 replicas."}
              ]))),

    ("TC-17", "🔄 Conversation Context", "Multi-turn conversation coherent",
     lambda: (lambda r: {"passed": len(r) > 20, "actual": r[:80]}
              )(_chat("what was the resolution?", [
                  {"role": "user", "content": "summarize INC-001"},
                  {"role": "assistant", "content": "INC-001 was a payment outage."},
                  {"role": "user", "content": "find similar incidents"},
                  {"role": "assistant", "content": "Similar incidents involve DB issues."}
              ]))),

    # Edge Cases
    ("TC-18", "🛡️ Edge Cases", "Empty message handled gracefully",
     lambda: (lambda r: {"passed": r.status_code == 200, "actual": f"HTTP {r.status_code}"}
              )(requests.post(f"{BACKEND_URL}/chat",
                              json={"message": "   ", "history": []}, timeout=15))),

    ("TC-19", "🛡️ Edge Cases", "Very long message handled",
     lambda: (lambda r: {"passed": r.status_code == 200, "actual": f"HTTP {r.status_code}"}
              )(requests.post(f"{BACKEND_URL}/chat",
                              json={"message": "status " + "payment-service " * 50,
                                    "history": []}, timeout=20))),

    ("TC-20", "🛡️ Edge Cases", "Invalid incident ID — friendly message",
     lambda: (lambda r: {"passed": any(k in r.lower() for k in
                                       ["not found", "no incident", "invalid",
                                        "doesn't exist", "does not exist", "cannot", "unavailable"]),
                         "actual": r[:80]}
              )(_chat("summarize incident INC-999"))),

    ("TC-21", "🛡️ Edge Cases", "Unknown service query handled",
     lambda: (lambda r: {"passed": len(r) > 10, "actual": r[:80]}
              )(_chat("what is the status of flying-pig-service?"))),

    ("TC-22", "🛡️ Edge Cases", "Missing history field defaults",
     lambda: (lambda r: {"passed": r.status_code == 200, "actual": f"HTTP {r.status_code}"}
              )(requests.post(f"{BACKEND_URL}/chat", json={"message": "hello"}, timeout=15))),

    ("TC-23", "🛡️ Edge Cases", "Response time under 10 seconds",
     lambda: (lambda start: (lambda r, d: {"passed": d < 10000,
                                           "actual": f"Response: {d}ms (limit: 10000ms)"}
                             )(_chat("show all service statuses"),
                               round((time.time() - start) * 1000)))(time.time())),
]


# ── Test runner thread ────────────────────────────────────────────────────────
def run_tests():
    time.sleep(1.5)  # Wait for browser to open
    test_state["status"] = "running"
    test_state["start_time"] = datetime.now().isoformat()

    for test_id, category, name, fn in ALL_TESTS:
        test_state["current_test"] = test_id
        start = time.time()
        try:
            result = fn()
            duration = round((time.time() - start) * 1000)
            passed = result.get("passed", False)
            actual = str(result.get("actual", ""))[:100]
        except Exception as e:
            duration = round((time.time() - start) * 1000)
            passed = False
            actual = f"ERROR: {str(e)[:80]}"

        test_state["results"].append({
            "id": test_id,
            "name": name,
            "category": category,
            "passed": passed,
            "actual": actual,
            "duration_ms": duration
        })
        test_state["completed"] += 1

        icon = "✅" if passed else "❌"
        print(f"  {icon} [{duration}ms] {test_id} — {name}")

    test_state["current_test"] = ""
    test_state["finished"] = True
    passed_count = sum(1 for r in test_state["results"] if r["passed"])
    print(f"\n{'='*55}")
    print(f"  RESULTS: {passed_count}/{len(ALL_TESTS)} passed ({round(passed_count/len(ALL_TESTS)*100)}%)")
    print(f"{'='*55}")
    print(f"\n  Browser page will stay open. Press Ctrl+C to stop.\n")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  ChatOps AI — Automated Test Runner")
    print("  BITS Pilani | MTech SE | Vaidya Rucha Sandeep")
    print("="*55)
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Total Tests: {len(ALL_TESTS)}")
    print("="*55)

    # Check backend first
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if r.status_code == 200:
            print("  ✅ Backend is online")
        else:
            print("  ❌ Backend returned error")
            sys.exit(1)
    except Exception:
        print("  ❌ Backend is offline!")
        print("  Please start it first: uvicorn backend.main:app --reload --port 8000")
        sys.exit(1)

    print("\n  🌐 Opening browser...")
    print("  📋 Running 23 tests live...\n")

    # Start HTTP server
    server = HTTPServer(("localhost", 8502), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open browser
    webbrowser.open("http://localhost:8502")

    # Run tests in background thread
    test_thread = threading.Thread(target=run_tests)
    test_thread.start()

    try:
        test_thread.join()
        # Keep server alive so browser can still see results
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.shutdown()
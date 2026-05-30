import streamlit as st
import requests
import json
import random
from datetime import datetime
from pathlib import Path

BACKEND_URL = "http://localhost:8000"

INCIDENTS = [
    {"id": "INC-001", "title": "Payment Service Outage", "service": "payment-service", "severity": "critical", "status": "resolved", "time": "2025-11-01 02:15"},
    {"id": "INC-002", "title": "Auth Service High Latency", "service": "auth-service", "severity": "high", "status": "resolved", "time": "2025-11-10 14:00"},
    {"id": "INC-003", "title": "Order Service Deployment Failure", "service": "order-service", "severity": "medium", "status": "resolved", "time": "2025-12-05 10:30"},
    {"id": "INC-004", "title": "Notification Service Memory Leak", "service": "notification-service", "severity": "high", "status": "resolved", "time": "2025-12-20 06:00"},
    {"id": "INC-005", "title": "API Gateway 502 Bad Gateway", "service": "api-gateway", "severity": "critical", "status": "resolved", "time": "2026-01-03 20:00"},
]

ACTION_LOG = [
    {"time": "2026-01-28 14:02", "action": "Deploy", "service": "order-service", "user": "ops-bot", "result": "success"},
    {"time": "2026-01-23 08:35", "action": "Restart", "service": "auth-service", "user": "ops-bot", "result": "success"},
    {"time": "2026-01-20 10:05", "action": "Scale ↑", "service": "payment-service", "user": "ops-bot", "result": "success"},
    {"time": "2026-01-10 16:20", "action": "Rollback", "service": "order-service", "user": "ops-bot", "result": "success"},
    {"time": "2026-01-03 20:22", "action": "Restart", "service": "config-service", "user": "ops-bot", "result": "success"},
]


def fetch_services() -> list:
    try:
        data_path = Path(__file__).parent.parent / "backend" / "data" / "services.json"
        with open(data_path) as f:
            return json.load(f)
    except Exception:
        return []


def generate_sparkline_data(base: int, points: int = 12) -> list:
    data = []
    val = base
    for _ in range(points):
        val = max(5, min(95, val + random.randint(-8, 8)))
        data.append(val)
    return data


def render_mini_chart(values: list, color: str = "#6b8ef5") -> str:
    if not values:
        return ""
    max_v = max(values) or 1
    min_v = min(values)
    height = 40
    width = 120
    points_count = len(values)
    step = width / (points_count - 1)

    pts = []
    for i, v in enumerate(values):
        x = i * step
        y = height - ((v - min_v) / (max_v - min_v + 1)) * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(pts)
    fill_pts = f"0,{height} " + polyline + f" {width},{height}"

    return f"""
    <svg width="{width}" height="{height}" style="display:block;">
        <defs>
            <linearGradient id="grad_{color[1:]}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
            </linearGradient>
        </defs>
        <polygon points="{fill_pts}" fill="url(#grad_{color[1:]})" />
        <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>
    """


def severity_badge(severity: str) -> str:
    colors = {
        "critical": ("#e05555", "#2e1515"),
        "high": ("#e08830", "#2e1e0a"),
        "medium": ("#c8a800", "#2a2200"),
        "low": ("#4aaa6e", "#0e2818"),
    }
    fg, bg = colors.get(severity, ("#888", "#1e1e2e"))
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:20px;font-size:0.76rem;font-weight:600;border:1px solid {fg}44;">{severity.upper()}</span>'


def status_indicator(status: str) -> str:
    if status == "healthy":
        return '<span style="color:#4aaa6e;">● </span><span style="color:#4aaa6e;font-weight:600;">Healthy</span>'
    elif status == "degraded":
        return '<span style="color:#e08830;">● </span><span style="color:#e08830;font-weight:600;">Degraded</span>'
    else:
        return '<span style="color:#e05555;">● </span><span style="color:#e05555;font-weight:600;">Critical</span>'


def render_dashboard():
    st.markdown("""
    <style>
        .stApp { background-color: #1a1f2e; }
        [data-testid="stSidebar"] { background-color: #141824; border-right: 1px solid #2e3650; }
        [data-testid="stSidebar"] * { color: #c9d1e0 !important; }
        [data-testid="stSidebar"] button {
            background-color: #252c42 !important;
            color: #c9d1e0 !important;
            border: 1px solid #3a4460 !important;
            border-radius: 8px !important;
        }
        .stApp p, .stApp li, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3 {
            color: #c9d1e0;
        }
        .metric-card {
            background: #212840;
            border: 1px solid #2e3a58;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
        }
        .service-card {
            background: #212840;
            border: 1px solid #2e3a58;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
        }
        .service-card-degraded { border-left: 4px solid #e08830 !important; }
        .service-card-critical { border-left: 4px solid #e05555 !important; }
        .service-card-healthy { border-left: 4px solid #4aaa6e !important; }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #6b8ef5;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #2e3650;
        }
        .stat-number { font-size: 2rem; font-weight: 700; color: #e4e9f5; }
        .stat-label { font-size: 0.78rem; color: #6a7a9a; text-transform: uppercase; letter-spacing: 0.05em; }
        hr { border-color: #2e3650 !important; }
        .progress-bar-bg {
            background: #2a3250;
            border-radius: 4px;
            height: 5px;
            width: 100%;
            margin-top: 4px;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            color: #6a7a9a !important; font-size: 0.76rem; text-transform: uppercase;
            letter-spacing: 0.05em; padding: 8px 12px;
            border-bottom: 1px solid #2e3650; text-align: left;
        }
        td {
            color: #c9d1e0 !important; font-size: 0.86rem;
            padding: 9px 12px; border-bottom: 1px solid #212840;
        }
        tr:hover td { background: #1e2438; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #1a1f2e; }
        ::-webkit-scrollbar-thumb { background: #3a4460; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

    services = fetch_services()
    if not services:
        st.error("Could not load service data.")
        return

    healthy = sum(1 for s in services if s["status"] == "healthy")
    degraded = sum(1 for s in services if s["status"] == "degraded")
    total = len(services)

    # Header
    st.markdown('<h1 style="color:#6b8ef5;margin-bottom:0;">📊 Operations Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6a7a9a;margin-top:4px;">Real-time system health and incident overview</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#3a4a6a;font-size:0.8rem;">Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
    st.divider()

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-card" style="border-left:4px solid #6b8ef5;">
            <div class="stat-label">Total Services</div>
            <div class="stat-number">{total}</div>
            <div style="color:#6a7a9a;font-size:0.78rem;margin-top:4px;">Across all teams</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card" style="border-left:4px solid #4aaa6e;">
            <div class="stat-label">Healthy</div>
            <div class="stat-number" style="color:#4aaa6e;">{healthy}</div>
            <div style="color:#4aaa6e;font-size:0.78rem;margin-top:4px;">Running normally</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card" style="border-left:4px solid #e08830;">
            <div class="stat-label">Degraded</div>
            <div class="stat-number" style="color:#e08830;">{degraded}</div>
            <div style="color:#e08830;font-size:0.78rem;margin-top:4px;">Needs attention</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="metric-card" style="border-left:4px solid #e05555;">
            <div class="stat-label">Total Incidents</div>
            <div class="stat-number" style="color:#e05555;">{len(INCIDENTS)}</div>
            <div style="color:#4aaa6e;font-size:0.78rem;margin-top:4px;">All resolved ✓</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown('<div class="section-title">🖥️ Service Health</div>', unsafe_allow_html=True)
        for svc in services:
            cpu = int(svc["cpu_usage"].replace("%", ""))
            mem = int(svc["memory_usage"].replace("%", ""))
            cpu_color = "#e05555" if cpu > 80 else "#e08830" if cpu > 60 else "#4aaa6e"
            mem_color = "#e05555" if mem > 80 else "#e08830" if mem > 60 else "#4aaa6e"
            card_class = f"service-card service-card-{svc['status']}"
            replicas = svc["replicas"]
            cpu_chart = render_mini_chart(generate_sparkline_data(cpu), cpu_color)

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                            <span style="font-weight:700;color:#e4e9f5;font-size:0.93rem;">{svc['name']}</span>
                            <span style="color:#3a4a6a;font-size:0.76rem;">{svc['version']}</span>
                            <span style="color:#3a4a6a;font-size:0.76rem;">| {svc['owner']}</span>
                        </div>
                        <div style="display:flex;gap:20px;align-items:center;">
                            <div>{status_indicator(svc['status'])}</div>
                            <div style="color:#6a7a9a;font-size:0.8rem;">
                                🔁 <b style="color:#c9d1e0;">{replicas['running']}/{replicas['desired']}</b> replicas
                            </div>
                            <div style="color:#6a7a9a;font-size:0.8rem;">
                                ⏱ <b style="color:#c9d1e0;">{svc['uptime']}</b>
                            </div>
                        </div>
                        <div style="display:flex;gap:24px;margin-top:10px;">
                            <div>
                                <span style="color:#6a7a9a;font-size:0.72rem;text-transform:uppercase;">CPU</span>
                                <div style="color:{cpu_color};font-weight:600;font-size:0.88rem;">{svc['cpu_usage']}</div>
                                <div class="progress-bar-bg">
                                    <div style="background:{cpu_color};height:5px;border-radius:4px;width:{cpu}%;"></div>
                                </div>
                            </div>
                            <div>
                                <span style="color:#6a7a9a;font-size:0.72rem;text-transform:uppercase;">Memory</span>
                                <div style="color:{mem_color};font-weight:600;font-size:0.88rem;">{svc['memory_usage']}</div>
                                <div class="progress-bar-bg">
                                    <div style="background:{mem_color};height:5px;border-radius:4px;width:{mem}%;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="margin-left:16px;opacity:0.9;">{cpu_chart}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-title">🚨 Incident History</div>', unsafe_allow_html=True)
        inc_rows = ""
        for inc in INCIDENTS:
            inc_rows += f"""
            <tr>
                <td><b style="color:#6b8ef5;">{inc['id']}</b></td>
                <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{inc['title']}</td>
                <td>{severity_badge(inc['severity'])}</td>
                <td><span style="color:#4aaa6e;">✓ resolved</span></td>
            </tr>"""
        st.markdown(f"""
        <div class="metric-card" style="padding:12px;">
            <table>
                <thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>Status</th></tr></thead>
                <tbody>{inc_rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="section-title">⚡ Action Log</div>', unsafe_allow_html=True)
        action_rows = ""
        for act in ACTION_LOG:
            result_color = "#4aaa6e" if act["result"] == "success" else "#e05555"
            action_rows += f"""
            <tr>
                <td style="color:#3a4a6a;font-size:0.76rem;">{act['time']}</td>
                <td><span style="color:#6b8ef5;font-weight:600;">{act['action']}</span></td>
                <td>{act['service']}</td>
                <td><span style="color:{result_color};">● {act['result']}</span></td>
            </tr>"""
        st.markdown(f"""
        <div class="metric-card" style="padding:12px;">
            <table>
                <thead><tr><th>Time</th><th>Action</th><th>Service</th><th>Result</th></tr></thead>
                <tbody>{action_rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="section-title">🔗 Service Dependencies</div>', unsafe_allow_html=True)
    dep_cols = st.columns(3)
    for i, svc in enumerate(services):
        if svc["dependencies"]:
            with dep_cols[i % 3]:
                deps_html = "".join([
                    f'<span style="background:#252c42;color:#8a9abf;padding:2px 8px;border-radius:4px;font-size:0.76rem;margin:2px;display:inline-block;">→ {d}</span>'
                    for d in svc["dependencies"]
                ])
                st.markdown(f"""
                <div class="metric-card" style="padding:12px 16px;">
                    <div style="font-weight:600;color:#c9d1e0;margin-bottom:6px;">{svc['name']}</div>
                    <div>{deps_html}</div>
                </div>""", unsafe_allow_html=True)
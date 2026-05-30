import json
import os
import re
from groq import Groq
from backend.services.devops_actions import (
    get_all_services, get_service_status, get_degraded_services,
    simulate_restart, simulate_scale, simulate_rollback
)
from backend.services.incident_analyzer import (
    load_incidents, get_incident_by_id, get_incidents_by_service,
    summarize_incident, analyze_logs_rca
)
from backend.services.knowledge_base import search_similar_incidents

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are DevOpsBot, an AI-powered ChatOps assistant for a DevOps team.
You help engineers ONLY with:
- Checking service health and status
- Analyzing incident logs and identifying root causes
- Simulating DevOps actions (restart, scale, rollback)
- Searching the knowledge base for similar past incidents
- Answering general DevOps, Kubernetes, Docker, CI/CD related questions

STRICT RULES:
- If the user asks anything NOT related to DevOps, software operations, infrastructure, or technology, politely decline and redirect them.
- For off-topic questions respond ONLY with: "I'm DevOpsBot and I'm only able to help with DevOps-related topics. Try asking me about service health, incidents, or deployments! 🤖"
- NEVER answer questions about food, diet, gym, fitness, personal advice, politics, entertainment, or any non-DevOps topic.
- NEVER use backticks around service names or status words
- For tables use markdown | pipe | format
- Use ✅ for healthy, ⚠️ for degraded, 🔴 for critical
- Be concise, technical, and helpful

STRICT FORMATTING RULES:
- NEVER use backticks around service names, status words, or any regular text
- NEVER wrap words in single backticks like `word` unless it is actual code or a command
- Use plain text for service names, statuses, IDs
- For tables, use markdown table format with | pipes |
- For status values use plain words: healthy, degraded, critical — no backticks
- Use **bold** only for headers or important labels
- Emojis are allowed: use ✅ for healthy, ⚠️ for degraded, 🔴 for critical
- Be concise, technical, and helpful

Current context data will be injected into your messages."""


def detect_intent(user_message: str) -> dict:
    prompt = f"""Classify this DevOps chatbot message into one of these intents:
- service_status: user wants to know about service health/status
- incident_summary: user wants a summary of a specific incident by ID
- rca_logs: user wants root cause analysis of pasted logs
- devops_action: user wants to restart/scale/rollback a service
- kb_search: user wants to find similar past incidents
- list_incidents: user wants to see incident history for a service or all
- general_question: general DevOps question or greeting

Message: "{user_message}"

Respond with valid JSON only, no markdown, no backticks:
{{"intent": "<intent>", "service": "<service name or null>", "incident_id": "<INC-XXX or null>", "action": "<restart|scale|rollback|null>", "replicas": null}}"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def build_context(intent: dict, user_message: str) -> str:
    ctx = ""
    i = intent.get("intent")
    service = intent.get("service")
    incident_id = intent.get("incident_id")

    if i == "service_status":
        if service and service != "null":
            svc = get_service_status(service)
            ctx = f"SERVICE DATA:\n{json.dumps(svc, indent=2)}" if svc else f"No service named '{service}' found."
        else:
            all_svcs = get_all_services()
            ctx = f"ALL SERVICES:\n{json.dumps(all_svcs, indent=2)}"

    elif i == "incident_summary" and incident_id and incident_id != "null":
        ctx = f"INCIDENT ANALYSIS:\n{summarize_incident(incident_id)}"

    elif i == "list_incidents":
        incidents = get_incidents_by_service(service) if service and service != "null" else load_incidents()
        summary = [{"id": inc["id"], "title": inc["title"], "service": inc["service"],
                    "severity": inc["severity"], "status": inc["status"]} for inc in incidents]
        ctx = f"INCIDENTS:\n{json.dumps(summary, indent=2)}"

    elif i == "devops_action" and service and service != "null":
        action = intent.get("action", "")
        if action == "restart":
            result = simulate_restart(service)
        elif action == "scale":
            replicas = intent.get("replicas") or 3
            result = simulate_scale(service, replicas)
        elif action == "rollback":
            result = simulate_rollback(service)
        else:
            result = {"message": "Unknown action."}
        ctx = f"ACTION RESULT:\n{json.dumps(result, indent=2)}"

    elif i == "kb_search":
        results = search_similar_incidents(user_message)
        ctx = f"SIMILAR PAST INCIDENTS:\n{json.dumps(results, indent=2)}"

    elif i == "rca_logs":
        analysis = analyze_logs_rca(user_message, service or "unknown")
        ctx = f"RCA ANALYSIS:\n{analysis}"

    return ctx


def chat(user_message: str, history: list[dict]) -> str:
    intent = detect_intent(user_message)
    context = build_context(intent, user_message)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for turn in history[-10:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    if context:
        enriched_message = f"{user_message}\n\n[CONTEXT DATA]\n{context}"
    else:
        enriched_message = user_message

    messages.append({"role": "user", "content": enriched_message})

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.4
    )
    return response.choices[0].message.content
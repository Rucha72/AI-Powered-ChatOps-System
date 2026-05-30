import json
import os
from pathlib import Path
from groq import Groq

DATA_DIR = Path(__file__).parent.parent / "data"

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


def load_incidents() -> list[dict]:
    with open(DATA_DIR / "incidents.json") as f:
        return json.load(f)


def get_incident_by_id(incident_id: str) -> dict | None:
    incidents = load_incidents()
    for inc in incidents:
        if inc["id"].lower() == incident_id.lower():
            return inc
    return None


def get_incidents_by_service(service_name: str) -> list[dict]:
    incidents = load_incidents()
    return [
        inc for inc in incidents
        if service_name.lower() in inc["service"].lower()
    ]


def summarize_incident(incident_id: str) -> str:
    inc = get_incident_by_id(incident_id)
    if not inc:
        return f"No incident found with ID '{incident_id}'."

    logs_text = "\n".join(inc["logs"])
    prompt = f"""You are a DevOps expert. Analyze the following incident and provide:
1. A concise 2-3 sentence summary of what happened
2. The probable root cause
3. The resolution applied
4. 2-3 recommendations to prevent recurrence

Incident ID: {inc['id']}
Title: {inc['title']}
Service: {inc['service']}
Severity: {inc['severity']}

Logs:
{logs_text}

Format your response clearly with headers for each section."""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


def analyze_logs_rca(raw_logs: str, service_name: str = "unknown") -> str:
    prompt = f"""You are a senior DevOps engineer performing root cause analysis.
Analyze the following logs from service '{service_name}' and provide:
1. Summary of what went wrong
2. Most probable root cause(s)
3. Recommended immediate actions
4. Long-term preventive measures

Logs:
{raw_logs}

Be specific and technical."""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
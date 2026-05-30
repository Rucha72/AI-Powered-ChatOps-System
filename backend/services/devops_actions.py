import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_services() -> list[dict]:
    with open(DATA_DIR / "services.json") as f:
        return json.load(f)


def get_all_services() -> list[dict]:
    return load_services()


def get_service_status(service_name: str) -> dict | None:
    services = load_services()
    name_lower = service_name.lower().strip()
    for svc in services:
        if svc["name"].lower() == name_lower or name_lower in svc["name"].lower():
            return svc
    return None


def get_degraded_services() -> list[dict]:
    return [s for s in load_services() if s["status"] != "healthy"]


def simulate_restart(service_name: str) -> dict:
    svc = get_service_status(service_name)
    if not svc:
        return {"success": False, "message": f"Service '{service_name}' not found."}
    return {
        "success": True,
        "message": f"✅ Simulated restart triggered for **{svc['name']}** (v{svc['version']}). "
                   f"Expected recovery time: ~60 seconds.",
        "service": svc["name"],
        "action": "restart"
    }


def simulate_scale(service_name: str, replicas: int) -> dict:
    svc = get_service_status(service_name)
    if not svc:
        return {"success": False, "message": f"Service '{service_name}' not found."}
    return {
        "success": True,
        "message": f"✅ Simulated scale for **{svc['name']}** → {replicas} replicas. "
                   f"(Currently running {svc['replicas']['running']}/{svc['replicas']['desired']})",
        "service": svc["name"],
        "action": "scale",
        "replicas": replicas
    }


def simulate_rollback(service_name: str) -> dict:
    svc = get_service_status(service_name)
    if not svc:
        return {"success": False, "message": f"Service '{service_name}' not found."}
    return {
        "success": True,
        "message": f"✅ Simulated rollback triggered for **{svc['name']}**. "
                   f"Rolling back from {svc['version']} to previous stable version.",
        "service": svc["name"],
        "action": "rollback"
    }

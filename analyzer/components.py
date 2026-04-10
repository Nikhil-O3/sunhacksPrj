from __future__ import annotations

import os
from typing import Any

COMPONENT_KEYWORDS = {
    "DB": ["db", "database", "sql", "postgres", "mongo", "redis", "sqlite", "schema", "dynamodb"],
    "AI/ML": ["ml", "model", "ai", "tensorflow", "pytorch", "sklearn", "predict", "analysis", "training", "inference"],
    "Processing": ["process", "pipeline", "batch", "worker", "queue", "compute", "service", "scheduler"],
    "Authentication": ["auth", "login", "oauth", "jwt", "session", "password", "token", "sso"],
    "UI": ["ui", "frontend", "react", "angular", "vue", "html", "css", "template", "view"],
    "UX": ["ux", "experience", "interface", "design", "layout", "navigation"],
}


def _load_file_text(repo_root: str | None, file_path: str) -> str:
    if not repo_root:
        return file_path.lower()
    candidate = os.path.join(repo_root, file_path)
    try:
        with open(candidate, "r", encoding="utf-8", errors="ignore") as handle:
            return (file_path + " " + handle.read()).lower()
    except Exception:
        return file_path.lower()


def _keyword_match(file_text: str, keywords: list[str]) -> bool:
    candidate = file_text.replace("_", " ").replace("-", " ")
    for keyword in keywords:
        if keyword in candidate:
            return True
    return False


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def analyze_system_components(files: list[dict[str, Any]], repo_root: str | None = None) -> list[dict[str, Any]]:
    if not files:
        return []

    max_complexity = max((item.get("complexity", 0) for item in files), default=1)
    overall_avg_risk = _average([item.get("risk_score", 0.0) for item in files])
    overall_avg_complexity = _average([item.get("complexity", 0) for item in files])
    overall_avg_maintainability = _average([item.get("maintainability", 0.0) for item in files])

    component_scores = []
    for component, keywords in COMPONENT_KEYWORDS.items():
        matched_files = []
        for item in files:
            file_key = item.get("file") or item.get("file_path") or ""
            text = _load_file_text(repo_root, file_key)
            if _keyword_match(text, keywords):
                matched_files.append(item)

        if matched_files:
            avg_risk = _average([item["risk_score"] for item in matched_files])
            avg_complexity = _average([item["complexity"] for item in matched_files])
            avg_maintainability = _average([item["maintainability"] for item in matched_files])
        else:
            avg_risk = overall_avg_risk
            avg_complexity = overall_avg_complexity
            avg_maintainability = overall_avg_maintainability

        complexity_factor = min(1.0, avg_complexity / max_complexity) if max_complexity > 0 else 0.0
        health_ratio = (
            (1.0 - avg_risk) * 0.55
            + (1.0 - complexity_factor) * 0.25
            + min(1.0, avg_maintainability / 100.0) * 0.2
        )
        health_score = round(max(0.0, min(1.0, health_ratio)) * 100, 1)

        component_scores.append(
            {
                "component": component,
                "health_score": health_score,
                "matched_files": len(matched_files),
                "avg_risk": round(avg_risk, 3),
                "avg_complexity": round(avg_complexity, 1),
                "avg_maintainability": round(avg_maintainability, 1),
            }
        )

    return component_scores

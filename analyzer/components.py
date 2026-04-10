from __future__ import annotations

import os
import re
from typing import Any

COMPONENT_KEYWORDS = {
    "DB": ["db", "database", "sql", "postgres", "mongo", "redis", "sqlite", "schema", "dynamodb", "prisma"],
    "Authentication": ["auth", "login", "oauth", "jwt", "session", "password", "token", "sso"],
    "UI": ["ui", "frontend", "react", "angular", "vue", "html", "css", "template"],
    "UX": ["ux", "experience", "interface", "design", "layout", "navigation"],
}

PATH_ONLY_KEYWORDS = {
    "DB": ["db"],
    "UI": ["ui"],
    "UX": ["ux"],
}


def _load_file_text(repo_root: str | None, file_path: str) -> str:
    if not repo_root:
        return ""
    candidate = os.path.join(repo_root, file_path)
    try:
        with open(candidate, "r", encoding="utf-8", errors="ignore") as handle:
            return handle.read().lower()
    except Exception:
        return ""


def _keyword_match(file_text: str, keywords: list[str]) -> bool:
    candidate = file_text.replace("_", " ").replace("-", " ")
    for keyword in keywords:
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        if re.search(pattern, candidate):
            return True
    return False


def _component_match(component: str, file_path: str, file_text: str) -> bool:
    keywords = COMPONENT_KEYWORDS[component]
    path_keywords = keywords + PATH_ONLY_KEYWORDS.get(component, [])
    source_keywords = [keyword for keyword in keywords if keyword not in PATH_ONLY_KEYWORDS.get(component, [])]

    return _keyword_match(file_path.lower(), path_keywords) or _keyword_match(file_text, source_keywords)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def analyze_system_components(files: list[dict[str, Any]], repo_root: str | None = None) -> list[dict[str, Any]]:
    if not files:
        return []

    max_complexity = max((item.get("complexity", 0) for item in files), default=1)

    component_scores = []
    for component in COMPONENT_KEYWORDS:
        matched_files = []
        for item in files:
            file_key = item.get("file") or item.get("file_path") or ""
            text = _load_file_text(repo_root, file_key)
            if _component_match(component, file_key, text):
                matched_files.append(item)

        if not matched_files:
            continue

        avg_risk = _average([item["risk_score"] for item in matched_files])
        avg_complexity = _average([item["complexity"] for item in matched_files])
        avg_maintainability = _average([item["maintainability"] for item in matched_files])
        avg_bug_resolution = _average([item.get("bug_resolution_rate", 0.0) for item in matched_files])

        complexity_factor = min(1.0, avg_complexity / max_complexity) if max_complexity > 0 else 0.0

        # Health score calculation with more variation
        # Base score starts at 60, adjusted by multiple factors
        base_health = 60

        # Risk penalty: lower risk = higher score (up to +25 points)
        risk_bonus = (1.0 - avg_risk) * 25

        # Complexity penalty: lower complexity = higher score (up to -15 points)
        complexity_penalty = complexity_factor * 15

        # Maintainability bonus: higher maintainability = higher score (up to +15 points)
        maintainability_bonus = min(1.0, avg_maintainability / 100.0) * 15

        # Bug resolution bonus: more bug fixes = higher score (up to +10 points)
        bug_resolution_bonus = min(1.0, avg_bug_resolution * 2) * 10  # Scale up the bug resolution impact

        health_score = round(max(10.0, min(99.0, base_health + risk_bonus - complexity_penalty + maintainability_bonus + bug_resolution_bonus)), 1)

        component_scores.append(
            {
                "component": component,
                "health_score": health_score,
                "matched_files": len(matched_files),
                "files": [item.get("file") or item.get("file_path") or "" for item in matched_files[:8]],
                "avg_risk": round(avg_risk, 3),
                "avg_complexity": round(avg_complexity, 1),
                "avg_maintainability": round(avg_maintainability, 1),
                "avg_bug_resolution_rate": round(avg_bug_resolution, 3),
            }
        )

    return sorted(component_scores, key=lambda entry: entry["health_score"])

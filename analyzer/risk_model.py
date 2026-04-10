import datetime


def normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    maximum = max(values)
    if maximum <= 0:
        return [0.0 for _ in values]
    return [float(v) / maximum for v in values]


def normalize_recency(dates: list[str]) -> list[float]:
    now = datetime.datetime.utcnow()
    days_since = []
    for raw in dates:
        if raw is None:
            days_since.append(None)
            continue
        try:
            date = datetime.datetime.fromisoformat(raw)
            days_since.append((now - date).days)
        except Exception:
            days_since.append(None)

    valid = [days for days in days_since if days is not None]
    if not valid:
        return [0.0 if days is None else 0.0 for days in days_since]
    maximum = max(valid)
    if maximum <= 0:
        return [1.0 if days is not None else 0.0 for days in days_since]
    return [1.0 - min(days, maximum) / maximum if days is not None else 0.0 for days in days_since]


def build_risk_report(files: list[dict]) -> list[dict]:
    complexities = [item.get("complexity", 0) for item in files]
    churns = [item.get("churn", 0) for item in files]
    contributors = [item.get("contributors", 0) for item in files]
    recencies = [item.get("last_commit_date") for item in files]

    weights = {
        "complexity": 0.4,
        "churn": 0.3,
        "contributors": 0.2,
        "recency": 0.1,
    }

    norm_complexity = normalize(complexities)
    norm_churn = normalize(churns)
    norm_contributors = normalize(contributors)
    norm_recency = normalize_recency(recencies)

    risk_items = []
    for index, item in enumerate(files):
        score = (
            weights["complexity"] * norm_complexity[index]
            + weights["churn"] * norm_churn[index]
            + weights["contributors"] * norm_contributors[index]
            + weights["recency"] * norm_recency[index]
        )
        risk_items.append(
            {
                "file": item["file_path"],
                "risk_score": round(score, 3),
                "complexity": item.get("complexity", 0),
                "maintainability": item.get("maintainability", 0.0),
                "churn": item.get("churn", 0),
                "contributors": item.get("contributors", 0),
                "last_commit_date": item.get("last_commit_date"),
            }
        )

    return sorted(risk_items, key=lambda entry: entry["risk_score"], reverse=True)

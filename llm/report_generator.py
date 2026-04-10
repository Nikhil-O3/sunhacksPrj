import os


def _load_env() -> None:
    env_file = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    env_file = os.path.abspath(env_file)
    if not os.path.isfile(env_file):
        return

    with open(env_file, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()


def _build_prompt(top_risky: list[dict], components: list[dict]) -> str:
    top_lines = []
    for item in top_risky:
        top_lines.append(
            f"- {item['file']}: risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']}"
        )

    component_lines = []
    for item in components:
        component_lines.append(
            f"- {item['component']}: health {item['health_score']} / 100, matched files {item['matched_files']}, avg risk {item['avg_risk']}"
        )

    return (
        "You are a senior technical advisor writing a detailed business report for a CEO.\n"
        "The repository has the following top risky modules:\n"
        + "\n".join(top_lines)
        + "\n\n"
        "The system also contains these component health scores:\n"
        + "\n".join(component_lines)
        + "\n\n"
        "Provide an executive summary, explain the main technical risks in business terms, estimate a hypothetical financial impact, "
        "and recommend corrective actions for each component. Keep the language executive-friendly, constructive, and concise."
    )


def _fake_report(top_risky: list[dict], components: list[dict]) -> str:
    report_lines = ["CEO Business Impact Report", "", "Top risky modules:"]
    for item in top_risky:
        report_lines.append(
            f"- {item['file']} (risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']})"
        )

    report_lines.append("")
    report_lines.append("System component health scores:")
    for item in components:
        report_lines.append(
            f"- {item['component']}: health {item['health_score']} / 100, matched files {item['matched_files']}, avg risk {item['avg_risk']}"
        )

    report_lines.extend(
        [
            "",
            "Executive summary:",
            "This repository analysis surfaces the most risky files and system components that could affect project delivery.",
            "Lower health scores indicate areas that deserve immediate attention, while higher scores reflect more stable subsystems.",
            "Estimated impact: poor component health can increase support costs, slow releases, and raise operational risk.",
            "Recommended actions: prioritize the top risky files, improve maintainability in weak components, and strengthen testing around DB, authentication, and UI flows.",
        ]
    )
    return "\n".join(report_lines)


def generate_ceo_report(top_risky: list[dict], overview: list[dict], components: list[dict]) -> str:
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("groq_api_key")
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")
    if not api_key or not top_risky:
        return _fake_report(top_risky, components)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        messages = [
            {"role": "system", "content": "You are a concise business report generator for a CEO."},
            {"role": "user", "content": _build_prompt(top_risky, components)},
        ]
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
        )

        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and isinstance(choice.message, dict):
                return choice.message.get("content", _fake_report(top_risky, components)).strip()
            if isinstance(choice, dict):
                return choice.get("message", {}).get("content", _fake_report(top_risky, components)).strip()

        return _fake_report(top_risky, components)
    except Exception:
        return _fake_report(top_risky, components)

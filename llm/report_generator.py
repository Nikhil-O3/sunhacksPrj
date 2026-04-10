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


def _build_prompt(top_risky: list[dict]) -> str:
    top_lines = []
    for item in top_risky:
        top_lines.append(
            f"- {item['file']}: risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']}"
        )
    return (
        "You are a senior technical advisor writing a concise business report for a CEO.\n"
        "The repository has the following top risky modules:\n"
        + "\n".join(top_lines)
        + "\n\n"
        "Please provide a simple overview of the main risks, explain why they matter to the business, estimate a hypothetical financial impact, "
        "and suggest corrective actions in plain English."
    )


def _fake_report(top_risky: list[dict]) -> str:
    report_lines = ["CEO Business Impact Report", ""]
    report_lines.append("Top risky modules:")
    for item in top_risky:
        report_lines.append(
            f"- {item['file']} (risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']})"
        )
    report_lines.extend(
        [
            "",
            "Summary:",
            "The highlighted modules are the most likely sources of delay or defects due to elevated complexity, churn, and team hand-offs.",
            "Estimated impact: higher maintenance costs, slower feature delivery, and increased operational risk if these files are not stabilized.",
            "Recommended actions: simplify the code, add automated tests, and allocate focused review effort on the top risky modules.",
        ]
    )
    return "\n".join(report_lines)


def generate_ceo_report(top_risky: list[dict], overview: list[dict]) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or not top_risky:
        return _fake_report(top_risky)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        messages = [
            {"role": "system", "content": "You are a concise business report generator for a CEO."},
            {"role": "user", "content": _build_prompt(top_risky)},
        ]
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
        )

        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and isinstance(choice.message, dict):
                return choice.message.get("content", _fake_report(top_risky)).strip()
            if isinstance(choice, dict):
                return choice.get("message", {}).get("content", _fake_report(top_risky)).strip()

        return _fake_report(top_risky)
    except Exception:
        return _fake_report(top_risky)

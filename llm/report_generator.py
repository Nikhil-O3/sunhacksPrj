import os
from typing import Any


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


def _extract_message_content(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not choices:
        return ""

    choice = choices[0]
    if isinstance(choice, dict):
        message = choice.get("message", {})
        if isinstance(message, dict):
            return str(message.get("content") or "").strip()
        return str(getattr(message, "content", "") or "").strip()

    message = getattr(choice, "message", None)
    if isinstance(message, dict):
        return str(message.get("content") or "").strip()
    return str(getattr(message, "content", "") or "").strip()


def _fallback_report(top_risky: list[dict], components: list[dict], reason: str = "") -> str:
    report = _fake_report(top_risky, components)
    if reason:
        report += f"\n\nLLM generation note: {reason}"
    return report


def _build_prompt(top_risky: list[dict], components: list[dict]) -> str:
    top_lines = []
    for item in top_risky:
        top_lines.append(
            f"- {item['file']}: risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']}, "
            f"Radon focus: {item.get('radon_focus_summary') or 'no Python blocks scored'}"
        )

    component_lines = []
    for item in components:
        component_lines.append(
            f"- {item['component']}: health {item['health_score']} / 100, matched files {item['matched_files']}, "
            f"avg risk {item['avg_risk']}, evidence files {item.get('files', [])}"
        )
    if not component_lines:
        component_lines.append("- No known system components were detected from repository paths or source keywords.")

    return (
        "You are a senior technical advisor writing a detailed business report for a CEO.\n"
        "The repository has the following top risky modules:\n"
        + "\n".join(top_lines)
        + "\n\n"
        "The system also contains these component health scores:\n"
        + "\n".join(component_lines)
        + "\n\n"
        "Provide an executive summary, explain the main technical risks in business terms, mention the Radon line ranges used for "
        "complexity scoring, estimate a hypothetical financial impact, and recommend corrective actions only for detected components. "
        "Do not invent DB, Authentication, UI, UX, or Processing sections if they were not detected. Keep the language "
        "executive-friendly, constructive, and concise."
    )


def _fake_report(top_risky: list[dict], components: list[dict]) -> str:
    report_lines = ["CEO Business Impact Report", "", "Top risky modules:"]
    for item in top_risky:
        report_lines.append(
            f"- {item['file']} (risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']})"
        )
        report_lines.append(f"  Radon focus: {item.get('radon_focus_summary') or 'no Python blocks scored'}")

    report_lines.append("")
    report_lines.append("Detected system component health scores:")
    if components:
        for item in components:
            files = ", ".join(item.get("files", [])) or "no file evidence recorded"
            report_lines.append(
                f"- {item['component']}: health {item['health_score']} / 100, matched files {item['matched_files']}, avg risk {item['avg_risk']}"
            )
            report_lines.append(f"  Evidence files: {files}")
    else:
        report_lines.append("- No known system components were detected from repository paths or source keywords.")

    report_lines.extend(
        [
            "",
            "Executive summary:",
            "This repository analysis surfaces the most risky files and system components that could affect project delivery.",
            "Lower health scores indicate detected areas that deserve attention, while absent components are intentionally not scored.",
            "Estimated impact: poor component health can increase support costs, slow releases, and raise operational risk.",
            "Recommended actions: prioritize the top risky files, improve maintainability in detected weak components, and add tests around the Radon-highlighted line ranges.",
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
        model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        messages = [
            {"role": "system", "content": "You are a concise business report generator for a CEO."},
            {"role": "user", "content": _build_prompt(top_risky, components)},
        ]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        content = _extract_message_content(response)
        if content:
            return content

        return _fallback_report(top_risky, components, "Groq returned an empty response.")
    except ImportError:
        return _fallback_report(top_risky, components, "Install the groq package to enable API report generation.")
    except Exception as exc:
        return _fallback_report(
            top_risky,
            components,
            f"Groq request failed with {type(exc).__name__}. Check GROQ_API_KEY and GROQ_MODEL.",
        )

import os
import shutil
import subprocess
import tempfile

from analyzer.components import analyze_system_components
from analyzer.git_miner import analyze_git_history, analyze_languages
from analyzer.metrics import compute_code_metrics_detail
from analyzer.predictive_model import predict_90_day_risks, estimate_cost_of_inaction
from analyzer.risk_model import build_risk_report
from llm.report_generator import generate_ceo_report


def clone_repo(repo_url: str, dest_dir: str) -> str:
    if not repo_url or not isinstance(repo_url, str):
        raise ValueError("Repository URL is required.")
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Only GitHub repository URLs are supported.")
    if shutil.which("git") is None:
        raise RuntimeError("git is required but not installed.")

    repo_dir = os.path.join(dest_dir, "repo")
    result = subprocess.run(
        ["git", "clone", repo_url, repo_dir],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repository: {result.stderr.strip()}")
    return repo_dir


def analyze_repository(repo_url: str) -> dict:
    temp_dir = tempfile.mkdtemp(prefix="pei_repo_")
    try:
        repo_dir = clone_repo(repo_url.strip(), temp_dir)
        files_data = analyze_git_history(repo_dir)
        if not files_data:
            raise ValueError("Repository contains no analyzed files or commit history.")

        enriched = []
        for item in files_data:
            file_path = os.path.join(repo_dir, item["file_path"])
            metrics = compute_code_metrics_detail(file_path)
            enriched.append(
                {
                    **item,
                    **metrics,
                }
            )

        risk_report = build_risk_report(enriched)
        component_health = analyze_system_components(risk_report, repo_dir)
        language_stats = analyze_languages(repo_dir)
        predictions = predict_90_day_risks(enriched, component_health)
        cost_analysis = estimate_cost_of_inaction(predictions['predictions'])
        top_risky = risk_report[:3]
        report = generate_ceo_report(top_risky, risk_report, component_health)

        return {
            "files": risk_report,
            "top_risky": top_risky,
            "components": component_health,
            "languages": language_stats,
            "predictions": predictions,
            "cost_analysis": cost_analysis,
            "report": report,
        }
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Analyze a GitHub repository for engineering risk.")
    parser.add_argument("repo_url", help="GitHub repository URL")
    args = parser.parse_args()

    output = analyze_repository(args.repo_url)
    print(json.dumps(output, indent=2))

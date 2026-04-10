# Predictive Engineering Intelligence Platform

A minimal prototype that analyzes a GitHub repository, computes code health metrics, scores risk per file, and generates a CEO-friendly report.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run frontend/app.py
```

## Usage

1. Enter a GitHub repository URL.
2. Click `Analyze Repository`.
3. The app shows:
   - a file-level risk table,
   - system component health scores,
   - top 3 risky files,
   - a CEO-style business impact report.
4. Click `Download Report as PDF` to save the report locally.

## Notes

- Set `GROQ_API_KEY` in the `.env` file or your shell environment to enable Groq report generation.
- Optionally set `GROQ_MODEL` to override the default Groq model (`llama-3.1-8b-instant`).
- If no API key is present, the platform returns a local fallback report.
- The system health section only shows components detected from repository paths or source keywords, such as DB, Processing, Authentication, UI, and UX.
- Python complexity and maintainability are calculated with Radon, including the function/class line ranges used for complexity scoring.
- The repository is cloned locally for analysis and removed after execution.

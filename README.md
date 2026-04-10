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
3. The app shows a risk table, top 3 risky files, and a CEO-style impact report.

## Notes

- Set `GROQ_API_KEY` in the `.env` file or your shell environment to enable Groq report generation.
- If no API key is present, the platform returns a local fallback report.
- The repository is cloned locally for analysis and removed after execution.

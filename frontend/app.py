import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import analyze_repository

st.set_page_config(page_title="Predictive Engineering Intelligence", layout="wide")
st.title("Predictive Engineering Intelligence Platform")

repo_url = st.text_input("GitHub repository URL", value="https://github.com/owner/repository")
if st.button("Analyze Repository"):
    if not repo_url or not repo_url.strip():
        st.error("Please enter a valid GitHub repository URL.")
    else:
        status = st.empty()
        status.info("Cloning and analyzing repository... This may take a moment.")
        try:
            result = analyze_repository(repo_url.strip())
            status.success("Analysis complete.")

            files = result.get("files", [])
            report = result.get("report", "")
            top_risky = result.get("top_risky", [])

            if not files:
                st.warning("No file data was returned. The repository may be empty or not accessible.")
            else:
                st.subheader("File Risk Scores")
                st.dataframe(files, use_container_width=True)

                st.subheader("Top 3 Risky Files")
                for item in top_risky:
                    st.markdown(
                        f"**{item['file']}** — risk {item['risk_score']}, complexity {item['complexity']}, churn {item['churn']}, contributors {item['contributors']}"
                    )

                st.subheader("CEO Business Impact Report")
                st.text_area("Report", report, height=320)
        except Exception as exc:
            status.error(f"Analysis failed: {exc}")

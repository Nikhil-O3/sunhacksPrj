import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import analyze_repository


def build_pdf(report_text: str, components: list[dict], top_risky: list[dict]) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Predictive Engineering Intelligence Report", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)

    pdf.cell(0, 6, "Top 3 Risky Files:", ln=True)
    pdf.set_font("Arial", "", 10)
    for item in top_risky:
        pdf.multi_cell(0, 6, f"- {item['file']} (risk {item['risk_score']}, complexity {item['complexity']})")
    pdf.ln(2)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "System Component Health Scores:", ln=True)
    pdf.set_font("Arial", "", 10)
    for component in components:
        pdf.multi_cell(
            0,
            6,
            f"- {component['component']}: {component['health_score']} / 100, matched files {component['matched_files']}, avg risk {component['avg_risk']}"
        )
    pdf.ln(4)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, report_text)
    return pdf.output(dest="S").encode("latin-1", "replace")


st.set_page_config(page_title="Predictive Engineering Intelligence", layout="wide")
st.title("Predictive Engineering Intelligence Platform")

CARD_STYLES = """
<style>
.card {border: 1px solid rgba(0,0,0,0.12); border-radius: 14px; padding: 16px; margin: 6px 0;}
.card-title {font-size: 16px; font-weight: 700; margin-bottom: 4px;}
.card-value {font-size: 28px; font-weight: 700; margin-bottom: 2px;}
.card-subtitle {font-size: 12px; color: #555; margin-bottom: 8px;}
.card-green {background: #e8f6ef; border-color: #6fcf97;}
.card-yellow {background: #fff8e6; border-color: #f2c94c;}
.card-red {background: #ffe8e8; border-color: #eb5757;}
.card-blue {background: #e8f0ff; border-color: #2f80ed;}
</style>
"""

st.markdown(CARD_STYLES, unsafe_allow_html=True)

repo_url = st.text_input("GitHub repository URL", value="https://github.com/Nikhil-O3/workoutTracker")
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
            components = result.get("components", [])
            report = result.get("report", "")
            top_risky = result.get("top_risky", [])

            if not files:
                st.warning("No file data was returned. The repository may be empty or not accessible.")
            else:
                st.subheader("Analytics")
                if components:
                    for i in range(0, len(components), 3):
                        cols = st.columns(3)
                        for comp, col in zip(components[i:i+3], cols):
                            score = comp["health_score"]
                            if score >= 80:
                                style = "card card-green"
                            elif score >= 55:
                                style = "card card-yellow"
                            else:
                                style = "card card-red"
                            col.markdown(
                                f"<div class='{style}'>"
                                f"<div class='card-title'>{comp['component']}</div>"
                                f"<div class='card-value'>{score} / 100</div>"
                                f"<div class='card-subtitle'>Matched files: {comp['matched_files']}</div>"
                                f"<div class='card-subtitle'>Avg risk: {comp['avg_risk']}, complexity {comp['avg_complexity']}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.info("No component health data was generated.")

                st.markdown("---")
                st.subheader("Risk Summary")
                left, right = st.columns([2, 1])

                with left:
                    st.markdown("**File risk table**")
                    st.dataframe(files, use_container_width=True)

                with right:
                    st.markdown("**Top 3 risky files**")
                    for item in top_risky:
                        st.markdown(
                            f"<div class='card card-blue'>"
                            f"<div class='card-title'>{item['file']}</div>"
                            f"<div class='card-value'>{item['risk_score']}</div>"
                            f"<div class='card-subtitle'>complexity {item['complexity']}, churn {item['churn']}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")
                st.subheader("Business Impact Report")
                st.text_area("Report", report, height=360)

                pdf_bytes = build_pdf(report, components, top_risky)
                if pdf_bytes:
                    st.download_button(
                        label="Download Report as PDF",
                        data=pdf_bytes,
                        file_name="pei_report.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.warning("PDF export is unavailable because the PDF library is not installed.")
        except Exception as exc:
            status.error(f"Analysis failed: {exc}")

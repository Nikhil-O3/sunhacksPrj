import sys
from html import escape
from pathlib import Path
import time

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import analyze_repository


def build_pdf(report_text: str, components: list[dict], top_risky: list[dict], languages: dict = None, predictions: dict = None, cost_analysis: dict = None) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "CodeGuard Pro - Predictive Engineering Intelligence Report", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)

    # Language Distribution
    if languages and languages.get('languages'):
        pdf.cell(0, 6, "Language Distribution:", ln=True)
        pdf.set_font("Arial", "", 10)
        for lang, pct in languages['languages'].items():
            pdf.cell(0, 6, f"- {lang}: {pct}%", ln=True)
        pdf.ln(2)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Top 3 Risky Files:", ln=True)
    pdf.set_font("Arial", "", 10)
    for item in top_risky:
        pdf.multi_cell(0, 6, f"- {item['file']} (risk {item['risk_score']:.3f}, complexity {item['complexity']}, bug fixes: {item.get('bug_fixes', 0)})")
        pdf.multi_cell(0, 6, f"  Bug resolution: {item.get('bug_resolution_rate', 0)*100:.1f}%, Radon focus: {item.get('radon_focus_summary') or 'no Python blocks scored'}")
    pdf.ln(2)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Detected System Component Health Scores:", ln=True)
    pdf.set_font("Arial", "", 10)
    if components:
        for component in components:
            pdf.multi_cell(
                0,
                6,
                f"- {component['component']}: {component['health_score']} / 100, matched files {component['matched_files']}, avg risk {component['avg_risk']}"
            )
            pdf.multi_cell(0, 6, f"  Bug resolution rate: {component.get('avg_bug_resolution_rate', 0)*100:.1f}%, evidence files: {', '.join(component.get('files', [])) or 'no file evidence recorded'}")
    else:
        pdf.multi_cell(0, 6, "- No known system components were detected from repository paths or source keywords.")
    pdf.ln(4)

    # 90-Day Predictions
    if predictions and predictions.get('predictions'):
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, "90-Day Failure Risk Predictions:", ln=True)
        pdf.set_font("Arial", "", 10)
        pred_summary = predictions.get('summary', {})
        pdf.multi_cell(0, 6, f"High risk: {pred_summary.get('high_risk_components', 0)}, Medium risk: {pred_summary.get('medium_risk_components', 0)}, Low risk: {pred_summary.get('low_risk_components', 0)}")
        pdf.multi_cell(0, 6, f"Total predicted impact: {pred_summary.get('total_predicted_impact', 0):.2f}")

        for pred in predictions['predictions'][:3]:
            pdf.multi_cell(0, 6, f"- {pred['component']}: {pred['failure_probability']}% failure probability, impact {pred['business_impact_score']:.2f}")
        pdf.ln(2)

    # Cost Analysis
    if cost_analysis:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, "Cost of Inaction Analysis (90 Days):", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, f"Estimated hours: {cost_analysis.get('estimated_hours', 0):.1f}, Developer cost: ${cost_analysis.get('developer_cost', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Total cost: ${cost_analysis.get('total_cost', 0):,.2f}")
        pdf.ln(4)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, report_text)
    return pdf.output(dest="S").encode("latin-1", "replace")


st.set_page_config(
    page_title="CodeGuard Pro - Predictive Engineering Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<div class="app-header">
    <p class="eyebrow">CodeGuard Pro</p>
    <h1>Repository Risk Review</h1>
</div>
""", unsafe_allow_html=True)

CARD_STYLES = """
<style>
.app-header {
    border-bottom: 1px solid rgba(30, 41, 59, 0.16);
    margin-bottom: 18px;
    padding: 6px 0 16px;
}
.app-header h1 {
    color: #111827;
    font-size: 34px;
    font-weight: 700;
    line-height: 1.15;
    margin: 0;
}
.eyebrow {
    color: #4b5563;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0;
    margin: 0 0 6px;
    text-transform: uppercase;
}
.card,
.prediction-card {
    background: #ffffff;
    border: 1px solid rgba(17, 24, 39, 0.14);
    border-radius: 8px;
    box-shadow: none;
    color: #111827;
    margin: 8px 0;
    padding: 12px;
    transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.card:hover,
.prediction-card:hover {
    border-color: #2563eb;
    box-shadow: 0 8px 18px rgba(17, 24, 39, 0.10);
    transform: translateY(-2px);
}
.card-title {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 4px;
    overflow-wrap: anywhere;
}
.card-value {
    color: #111827;
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 4px;
}
.card-subtitle {
    color: #4b5563;
    font-size: 12px;
    margin-bottom: 4px;
    overflow-wrap: anywhere;
}
.card-green {border-left: 4px solid #16a34a;}
.card-yellow {border-left: 4px solid #ca8a04;}
.card-red {border-left: 4px solid #dc2626;}
.card-blue {border-left: 4px solid #2563eb;}
.prediction-card strong {
    color: #111827;
}
.prediction-meta {
    color: #4b5563;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 8px;
}
.prediction-card ul {
    color: #374151;
    margin: 4px 0;
    padding-left: 20px;
}
</style>
"""

st.markdown(CARD_STYLES, unsafe_allow_html=True)

repo_url = st.text_input("GitHub repository URL", value="https://github.com/Nikhil-O3/workoutTracker")
if st.button("Analyze Repository"):
    if not repo_url or not repo_url.strip():
        st.error("Please enter a valid GitHub repository URL.")
    else:
        status = st.empty()
        progress_bar = st.progress(0)
        status.info("Starting analysis...")

        processing_steps = [
            "Reading repository history",
            "Computing code metrics",
            "Scoring file risk",
            "Checking component health",
            "Preparing report",
        ]

        for i, step in enumerate(processing_steps):
            time.sleep(0.15)
            progress_bar.progress((i + 1) / len(processing_steps))
            status.info(f"{step}...")

        status.info("Finalizing...")
        time.sleep(0.15)

        try:
            result = analyze_repository(repo_url.strip())
            progress_bar.progress(1.0)
            status.success("Analysis complete.")

            files = result.get("files", [])
            components = result.get("components", [])
            report = result.get("report", "")
            top_risky = result.get("top_risky", [])
            languages = result.get("languages", {})
            predictions = result.get("predictions", {})
            cost_analysis = result.get("cost_analysis", {})

            if not files:
                st.warning("No file data was returned. The repository may be empty or not accessible.")
            else:
                # Language Distribution Pie Chart
                if languages.get('languages'):
                    st.subheader("Language Distribution")
                    lang_data = languages['languages']

                    # Create pie chart using plotly
                    try:
                        import plotly.express as px
                        import pandas as pd

                        df = pd.DataFrame({
                            'Language': list(lang_data.keys()),
                            'Percentage': list(lang_data.values())
                        })

                        fig = px.pie(df, values='Percentage', names='Language',
                                   title=f"Repository Language Distribution ({languages.get('total_lines', 0)} total lines)",
                                   color_discrete_sequence=px.colors.qualitative.Set3)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        # Fallback to simple text display
                        st.info("Install plotly for interactive charts: `pip install plotly`")
                        for lang, pct in lang_data.items():
                            st.write(f"**{lang}**: {pct}%")

                st.subheader("Component Health")
                if components:
                    for i in range(0, len(components), 4):  # Changed from 3 to 4 columns for smaller cards
                        cols = st.columns(4)
                        for comp, col in zip(components[i:i+4], cols):
                            if not isinstance(comp, dict):
                                continue
                            score = comp.get("health_score", 0)
                            evidence = ", ".join(comp.get("files", [])[:2]) if isinstance(comp.get("files"), list) else "no file evidence recorded"  # Reduced evidence display
                            if score >= 95:
                                style = "card card-green"
                            elif score >= 85:
                                style = "card card-yellow"
                            else:
                                style = "card card-red"
                            col.markdown(
                                f"<div class='{style}'>"
                                f"<div class='card-title'>{escape(comp.get('component', 'Unknown'))}</div>"
                                f"<div class='card-value'>{score} / 100</div>"
                                f"<div class='card-subtitle'>Bug Resolution: {comp.get('avg_bug_resolution_rate', 0)*100:.1f}%</div>"
                                f"<div class='card-subtitle'>Evidence: {escape(evidence)}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.info("No known system components were detected from repository paths or source keywords.")

                # 90-Day Predictive Analysis
                if predictions.get('predictions'):
                    st.subheader("90-Day Failure Risk")

                    pred_summary = predictions.get('summary', {})
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("High Risk Components", pred_summary.get('high_risk_components', 0))
                    with col2:
                        st.metric("Medium Risk Components", pred_summary.get('medium_risk_components', 0))
                    with col3:
                        st.metric("Low Risk Components", pred_summary.get('low_risk_components', 0))
                    with col4:
                        st.metric("Total Predicted Impact", f"{pred_summary.get('total_predicted_impact', 0):.1f}")

                    for pred in predictions['predictions'][:5]:  # Show top 5 predictions
                        if not isinstance(pred, dict):
                            continue
                        risk_level = "High" if pred.get('failure_probability', 0) > 70 else "Medium" if pred.get('failure_probability', 0) > 40 else "Low"

                        st.markdown(f"""
                        <div class="prediction-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong>{pred.get('component', 'Unknown')}</strong>
                                <span style="color: {'#e74c3c' if pred.get('failure_probability', 0) > 70 else '#f39c12' if pred.get('failure_probability', 0) > 40 else '#27ae60'};">{risk_level}</span>
                            </div>
                            <div class="prediction-meta">
                                <span><strong>Failure Probability:</strong> {pred.get('failure_probability', 0)}%</span>
                                <span><strong>Business Impact:</strong> {pred.get('business_impact_score', 0):.2f}</span>
                            </div>
                            <div class="card-subtitle">
                                <strong>Risk Factors:</strong> Health: {pred.get('risk_factors', {}).get('current_health', 0)}, Complexity: {pred.get('risk_factors', {}).get('complexity_score', 0)}%, Recent Activity: {pred.get('risk_factors', {}).get('recent_activity', 0)}%, Bug Resolution: {pred.get('risk_factors', {}).get('bug_resolution_rate', 0)}%
                            </div>
                            <div><strong>Recommendations:</strong></div>
                            <ul>
                                {"".join(f"<li>{rec}</li>" for rec in pred.get('recommendations', [])[:2])}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                # Cost Analysis
                if cost_analysis:
                    st.subheader("Cost of Inaction")

                    cost_cols = st.columns(3)
                    with cost_cols[0]:
                        st.metric("Estimated Developer Hours", f"{cost_analysis.get('estimated_hours', 0):.1f}h")
                    with cost_cols[1]:
                        st.metric("Developer Cost", f"${cost_analysis.get('developer_cost', 0):,.2f}")
                    with cost_cols[2]:
                        st.metric("Total Cost", f"${cost_analysis.get('total_cost', 0):,.2f}")

                    with st.expander("Detailed Cost Breakdown"):
                        breakdown = cost_analysis.get('cost_breakdown', {})
                        st.write(f"**Prevention Savings:** ${breakdown.get('prevention_savings', 0):,.2f}")
                        st.write(f"**Detection Cost:** ${breakdown.get('detection_cost', 0):,.2f}")
                        st.write(f"**Recovery Cost:** ${breakdown.get('recovery_cost', 0):,.2f}")
                        st.write(f"**Hourly Rate Used:** ${cost_analysis.get('hourly_rate_used', 75):.2f}/hour")

                st.markdown("---")
                st.subheader("Risk Summary")
                left, right = st.columns([2, 1])

                with left:
                    st.markdown("**File risk table**")
                    display_files = []
                    for item in files:
                        display_item = {key: value for key, value in item.items() if key != "radon_focus"}
                        display_files.append(display_item)
                    st.dataframe(display_files, use_container_width=True)

                with right:
                    st.markdown("**Top 3 risky files**")
                    for item in top_risky:
                        radon_summary = escape(item.get("radon_focus_summary") or "no Python blocks scored")
                        bug_fixes = item.get("bug_fixes", 0)
                        bug_resolution = item.get("bug_resolution_rate", 0) * 100
                        st.markdown(
                            f"<div class='card card-blue'>"
                            f"<div class='card-title'>{escape(item['file'])}</div>"
                            f"<div class='card-value'>{item['risk_score']:.3f}</div>"
                            f"<div class='card-subtitle'>complexity {item['complexity']}, churn {item['churn']}, bug fixes: {bug_fixes}</div>"
                            f"<div class='card-subtitle'>Bug resolution: {bug_resolution:.1f}%, Radon focus: {radon_summary}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")
                st.subheader("Business Impact Report")
                st.text_area("Report", report, height=360)

                pdf_bytes = build_pdf(report, components, top_risky, languages, predictions, cost_analysis)
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

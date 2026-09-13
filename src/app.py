import streamlit as st
import sys
import os

# ============================================================
# INNOMINDS — SIF INTELLIGENCE ENGINE
# Streamlit Prototype
# ============================================================

# Make sure src folder is available for imports
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ------------------------------------------------------------
# Import our existing AI components
# ------------------------------------------------------------

from pipeline import analyze_report
from rule_mapper import map_life_saving_rule


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="INNOMINDS SIF Intelligence Engine",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .risk-high {
        background-color: #ffe5e5;
        padding: 18px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #ffb3b3;
    }

    .risk-low {
        background-color: #e8f5e9;
        padding: 18px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #b7dfb9;
    }

    .section-title {
        font-size: 24px;
        font-weight: 650;
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🛡️ INNOMINDS</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered SIF Intelligence & Safety Risk Prioritization'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# DEMO REPORTS
# ============================================================

DEMO_REPORTS = {

    "Energy Isolation":
        """
        During maintenance of a compressor, the equipment was shut down.
        The isolation valve was closed but the isolation was not verified.
        Residual pressure remained inside the process line.
        Two workers started removing the flange while standing close to the line.
        The supervisor noticed the unsafe condition and immediately stopped the work.
        The permit was reviewed and the isolation was verified before work resumed.
        """,

    "Confined Space":
        """
        During maintenance, a worker entered a storage tank before atmospheric
        testing was completed. Oxygen levels were not verified and ventilation
        was not operating properly. The worker was exposed to a potentially
        hazardous atmosphere inside the confined space.
        """,

    "Hot Work":
        """
        Welding was started near a hydrocarbon process line during maintenance.
        The area had not been adequately gas tested and flammable vapours were
        detected near the work location. The hot work was stopped after the
        unsafe condition was identified.
        """,

    "Line of Fire / Lifting":
        """
        During crane lifting operations, a worker entered the exclusion zone
        beneath a suspended load. The load shifted unexpectedly while being
        positioned and moved toward the worker. The lifting operation was
        immediately stopped.
        """,

    "Working at Height":
        """
        A worker was performing maintenance on an elevated platform without
        properly connecting the fall protection lanyard. The worker was close
        to an unprotected edge and could have fallen to the ground below.
        """
}


# ============================================================
# REPORT INPUT
# ============================================================

st.markdown(
    '<div class="section-title">📝 Safety Report Analysis</div>',
    unsafe_allow_html=True
)

input_mode = st.radio(
    "Select input mode",
    ["Enter Report", "Demo Scenario"],
    horizontal=True
)


if input_mode == "Demo Scenario":

    selected_demo = st.selectbox(
        "Choose a safety scenario",
        list(DEMO_REPORTS.keys())
    )

    report_text = st.text_area(
        "Safety report",
        value=DEMO_REPORTS[selected_demo].strip(),
        height=190
    )

else:

    report_text = st.text_area(
        "Enter a safety observation, near-miss or incident report:",
        height=190,
        placeholder=(
            "Example: During maintenance, the isolation was not verified "
            "before removing a flange..."
        )
    )


# ============================================================
# ANALYZE BUTTON
# ============================================================

analyze_button = st.button(
    "🔍 ANALYZE REPORT",
    type="primary",
    use_container_width=True
)


# ============================================================
# ANALYSIS
# ============================================================

if analyze_button:

    if not report_text.strip():

        st.warning(
            "Please enter a safety report before analysis."
        )

    else:

        with st.spinner(
            "AI is analyzing the safety report..."
        ):

            try:

                # --------------------------------------------
                # 1. Complete existing pipeline
                # --------------------------------------------

                result = analyze_report(
                    report_text
                )

                # --------------------------------------------
                # 2. Life-Saving Rule mapping
                # --------------------------------------------

                rules = map_life_saving_rule(
                    report_text,
                    top_k=3
                )

            except Exception as e:

                st.error(
                    f"Analysis failed: {e}"
                )

                st.stop()


        # ====================================================
        # SIF RESULT
        # ====================================================

        sif = result["sif_classification"]

        sif_label = sif["label"]
        confidence = sif["confidence"]

        if sif_label == "SIF-POTENTIAL":

            risk_text = "HIGH"
            risk_class = "risk-high"

        else:

            risk_text = "LOW"
            risk_class = "risk-low"


        # ====================================================
        # TOP RULE
        # ====================================================

        if rules:

            top_rule = rules[0]["rule"]
            top_similarity = rules[0]["similarity"]

        else:

            top_rule = "Unknown"
            top_similarity = 0


        # ====================================================
        # TOP EVENT
        # ====================================================

        events = result["events"]

        if events:

            event = events[0]

            activity = event["activity"]
            hazard = event["hazard"]
            barrier = event["barrier_failure"]
            consequence = event["consequence"]
            relevance = event["relevance"]

        else:

            activity = "Not detected"
            hazard = "Not detected"
            barrier = "Not detected"
            consequence = "Not detected"
            relevance = 0


        # ====================================================
        # RESULT SUMMARY
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">🎯 AI Analysis Result</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"""
                <div class="{risk_class}">
                    <div>SIF POTENTIAL</div>
                    <h2>{risk_text}</h2>
                    <div>{sif_label}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.metric(
                "Model Confidence",
                f"{confidence * 100:.1f}%"
            )

        with col3:

            st.metric(
                "Detected Events",
                result["event_count"]
            )


        # ====================================================
        # LIFE-SAVING RULE
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">🛡️ Life-Saving Rule Mapping</div>',
            unsafe_allow_html=True
        )

        rule_col1, rule_col2 = st.columns([2, 1])

        with rule_col1:

            st.success(
                f"Primary Life-Saving Rule: **{top_rule}**"
            )

        with rule_col2:

            st.metric(
                "Semantic Similarity",
                f"{top_similarity:.3f}"
            )


        # Show top 3 rules

        st.write("**Top Rule Matches:**")

        for rank, rule in enumerate(
            rules,
            start=1
        ):

            st.write(
                f"{rank}. **{rule['rule']}** — "
                f"similarity: {rule['similarity']:.3f}"
            )


        # ====================================================
        # STRUCTURED EVENT
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">🔎 Detected Safety Event</div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write("**Activity**")
            st.info(activity)

            st.write("**Hazard**")
            st.info(hazard)

        with col2:

            st.write("**Barrier Failure**")
            st.warning(barrier)

            st.write("**Potential Consequence**")
            st.error(consequence)


        # ====================================================
        # EVENT RELEVANCE
        # ====================================================

        st.write("")

        st.progress(
            max(0.0, min(float(relevance), 1.0))
        )

        st.caption(
            f"Semantic event relevance: {relevance:.3f}"
        )


        # ====================================================
        # EVIDENCE
        # ====================================================

        if events:

            st.divider()

            st.markdown(
                '<div class="section-title">📌 Evidence Sentences</div>',
                unsafe_allow_html=True
            )

            for sentence in event["evidence"]:

                st.write(
                    f"• {sentence}"
                )


        # ====================================================
        # PRECURSOR PATTERN
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">📊 Precursor Pattern</div>',
            unsafe_allow_html=True
        )

        st.code(
            f"{activity} → {hazard} → {barrier}",
            language="text"
        )

        st.caption(
            "This precursor chain connects the activity, hazard "
            "and failed barrier identified by the NLP pipeline."
        )


        # ====================================================
        # PRIORITY RECOMMENDATION
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">🚨 HSE Priority</div>',
            unsafe_allow_html=True
        )

        if sif_label == "SIF-POTENTIAL":

            st.error(
                "HIGH PRIORITY — This report should be reviewed "
                "promptly by HSE personnel because it contains "
                "potentially serious/fatal exposure indicators."
            )

        else:

            st.success(
                "LOWER PRIORITY — No strong SIF-potential signal "
                "was identified by the current prototype model."
            )
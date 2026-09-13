import streamlit as st
import sys
import os
import pandas as pd
import re


# ============================================================
# INNOMINDS — SIF INTELLIGENCE ENGINE
# ============================================================

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ------------------------------------------------------------
# Existing AI components
# ------------------------------------------------------------

from pipeline import analyze_report
from rule_mapper import map_life_saving_rule


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="INNOMINDS SIF Intelligence Engine",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CSS
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
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 10px;
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


# ============================================================
# LOAD DATA
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "osha_4470_prepared.csv"
)


@st.cache_data
def load_dataset():

    if not os.path.exists(DATA_PATH):
        return None

    data = pd.read_csv(
        DATA_PATH
    )

    return data


df = load_dataset()


# ============================================================
# TABS
# ============================================================

tab1, tab2 = st.tabs(
    [
        "🔍 Report Analyzer",
        "📊 Risk Dashboard"
    ]
)


# ============================================================
# TAB 1 — REPORT ANALYZER
# ============================================================

with tab1:

    st.markdown(
        '<div class="section-title">'
        '📝 Safety Report Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DEMO REPORTS
    # --------------------------------------------------------

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

    input_mode = st.radio(
        "Select input mode",
        [
            "Enter Report",
            "Demo Scenario"
        ],
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
                "Example: During maintenance, the isolation was not "
                "verified before removing a flange..."
            )
        )

    analyze_button = st.button(
        "🔍 ANALYZE REPORT",
        type="primary",
        use_container_width=True
    )


    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

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

                    result = analyze_report(
                        report_text
                    )

                    rules = map_life_saving_rule(
                        report_text,
                        top_k=3
                    )

                except Exception as e:

                    st.error(
                        f"Analysis failed: {e}"
                    )

                    st.stop()


            # ------------------------------------------------
            # SIF
            # ------------------------------------------------

            sif = result[
                "sif_classification"
            ]

            sif_label = sif["label"]

            score = sif["confidence"]


            if sif_label == "SIF-POTENTIAL":

                risk_text = "HIGH"

                risk_class = "risk-high"

            else:

                risk_text = "LOW"

                risk_class = "risk-low"


            # ------------------------------------------------
            # LIFE-SAVING RULE
            # ------------------------------------------------

            if rules:

                top_rule = rules[0]["rule"]

                top_similarity = rules[0]["similarity"]

            else:

                top_rule = "Unknown"

                top_similarity = 0


            # ------------------------------------------------
            # EVENT
            # ------------------------------------------------

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


            # =================================================
            # RESULT
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-title">'
                '🎯 AI Analysis Result'
                '</div>',
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
                    "SIF Model Score",
                    f"{score * 100:.1f}%"
                )

            with col3:

                st.metric(
                    "Detected Events",
                    result["event_count"]
                )


            # =================================================
            # LIFE-SAVING RULE
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-title">'
                '🛡️ Life-Saving Rule Mapping'
                '</div>',
                unsafe_allow_html=True
            )

            rule_col1, rule_col2 = st.columns(
                [2, 1]
            )

            with rule_col1:

                st.success(
                    f"Primary Life-Saving Rule: "
                    f"**{top_rule}**"
                )

            with rule_col2:

                st.metric(
                    "Semantic Similarity",
                    f"{top_similarity:.3f}"
                )


            st.write(
                "**Top Rule Matches:**"
            )

            for rank, rule in enumerate(
                rules,
                start=1
            ):

                st.write(
                    f"{rank}. **{rule['rule']}** — "
                    f"similarity: "
                    f"{rule['similarity']:.3f}"
                )


            # =================================================
            # EVENT
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-title">'
                '🔎 Detected Safety Event'
                '</div>',
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


            st.progress(
                max(
                    0.0,
                    min(
                        float(relevance),
                        1.0
                    )
                )
            )

            st.caption(
                f"Semantic event relevance: "
                f"{relevance:.3f}"
            )


            # =================================================
            # EVIDENCE
            # =================================================

            if events:

                st.divider()

                st.markdown(
                    '<div class="section-title">'
                    '📌 Evidence Sentences'
                    '</div>',
                    unsafe_allow_html=True
                )

                for sentence in event["evidence"]:

                    st.write(
                        f"• {sentence}"
                    )


            # =================================================
            # PRECURSOR
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-title">'
                '📊 Precursor Pattern'
                '</div>',
                unsafe_allow_html=True
            )

            st.code(
                f"{activity} → {hazard} → {barrier}",
                language="text"
            )


            # =================================================
            # HSE PRIORITY
            # =================================================

            st.divider()

            st.markdown(
                '<div class="section-title">'
                '🚨 HSE Priority'
                '</div>',
                unsafe_allow_html=True
            )

            if sif_label == "SIF-POTENTIAL":

                st.error(
                    "HIGH PRIORITY — This report should be "
                    "reviewed promptly by HSE personnel."
                )

            else:

                st.success(
                    "LOWER PRIORITY — No strong SIF signal "
                    "was identified by the current model."
                )


# ============================================================
# TAB 2 — RISK DASHBOARD
# ============================================================

with tab2:

    st.markdown(
        '<div class="section-title">'
        '📊 Safety Risk Intelligence Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    if df is None:

        st.error(
            "Prepared dataset not found."
        )

        st.info(
            "Expected file: "
            "data/processed/osha_4470_prepared.csv"
        )

        st.stop()


    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    total_reports = len(df)

    sif_reports = int(
        (df["sif_label"] == 1).sum()
    )

    non_sif_reports = int(
        (df["sif_label"] == 0).sum()
    )

    sif_percentage = (
        sif_reports / total_reports * 100
        if total_reports > 0
        else 0
    )


    st.caption(
        "Prototype analytics based on weak development "
        "labels from the public OSHA dataset. These are "
        "not OIL SIF prevalence estimates."
    )


    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Reports",
            f"{total_reports:,}"
        )

    with col2:

        st.metric(
            "SIF Development Flags",
            f"{sif_reports:,}"
        )

    with col3:

        st.metric(
            "Non-SIF Development Flags",
            f"{non_sif_reports:,}"
        )

    with col4:

        st.metric(
            "Flagged %",
            f"{sif_percentage:.1f}%"
        )


    # ========================================================
    # SIF DISTRIBUTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🎯 SIF Development-Flag Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    distribution = pd.DataFrame(
        {
            "Classification": [
                "SIF-Potential Flag",
                "Non-SIF Flag"
            ],
            "Reports": [
                sif_reports,
                non_sif_reports
            ]
        }
    )

    st.bar_chart(
        distribution.set_index(
            "Classification"
        )
    )


    # ========================================================
    # INDICATOR COUNTS
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '⚠️ Safety Hazard Indicators'
        '</div>',
        unsafe_allow_html=True
    )


    indicator_patterns = {

        "Fatality":
            r"fatality",

        "Fall From Height":
            r"fall_from_height",

        "Struck By":
            r"struck_by",

        "Caught Between":
            r"caught_between",

        "Electrical":
            r"electrical",

        "Fire / Explosion":
            r"fire_explosion",

        "Confined Space":
            r"confined_space",

        "Lifting":
            r"lifting",

        "Energy Release":
            r"energy_release",

        "Amputation":
            r"amputation"
    }


    indicator_counts = {}

    indicator_text = (
        df["sif_indicators"]
        .fillna("")
        .astype(str)
        .str.lower()
    )


    for name, pattern in indicator_patterns.items():

        indicator_counts[name] = int(
            indicator_text.str.contains(
                pattern,
                regex=True,
                na=False
            ).sum()
        )


    indicator_df = pd.DataFrame(
        {
            "Indicator": list(
                indicator_counts.keys()
            ),
            "Reports": list(
                indicator_counts.values()
            )
        }
    )

    indicator_df = indicator_df.sort_values(
        "Reports",
        ascending=False
    )


    st.bar_chart(
        indicator_df.set_index(
            "Indicator"
        )
    )


    # ========================================================
    # ACTIVITY / HAZARD / BARRIER EXTRACTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🔎 Recurring Safety Concepts'
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # Combine searchable text
    # --------------------------------------------------------

    searchable_text = (
        df["report_text"]
        .fillna("")
        .astype(str)
        .str.lower()
    )


    # ========================================================
    # ACTIVITY DETECTION
    # ========================================================

    activity_patterns = {

        "Maintenance":
            r"maintenance|repair|servicing|service",

        "Lifting":
            r"crane|lifting|hoist|sling|suspended load",

        "Work at Height":
            r"roof|scaffold|ladder|tower|elevated|height|fall",

        "Electrical Work":
            r"electrical|electrician|power line|energized|voltage|electroc",

        "Confined Space":
            r"confined space|tank|vessel|crawl space|manhole",

        "Hot Work":
            r"welding|welder|cutting|grinding|hot work",

        "Driving / Vehicle":
            r"vehicle|truck|forklift|pickup|tractor|motor vehicle|traffic",

        "Excavation":
            r"trench|excavation|excavated|cave-in"
    }


    activity_counts = {}

    for name, pattern in activity_patterns.items():

        activity_counts[name] = int(
            searchable_text.str.contains(
                pattern,
                regex=True,
                na=False
            ).sum()
        )


    activity_df = pd.DataFrame(
        {
            "Activity": list(
                activity_counts.keys()
            ),
            "Reports": list(
                activity_counts.values()
            )
        }
    )

    activity_df = activity_df.sort_values(
        "Reports",
        ascending=False
    )


    # ========================================================
    # HAZARD DETECTION
    # ========================================================

    hazard_patterns = {

        "Fall":
            r"fall|fell|falling",

        "Stored Energy":
            r"pressure|hydraulic|stored energy|unexpected movement",

        "Electrical Energy":
            r"electrical|electric|energized|voltage|power line|electroc",

        "Suspended Load":
            r"suspended|crane|hoist|sling|load",

        "Moving Equipment":
            r"forklift|vehicle|truck|tractor|machinery|moving equipment",

        "Fire / Explosion":
            r"explosion|explosive|fire|flammable|vapour|vapor|ignition",

        "Toxic Atmosphere":
            r"oxygen|toxic|gas|carbon monoxide|fumes|vapour|vapor",

        "Caught-in / Pinch":
            r"caught|crushed|pinned|entangled|amputation"
    }


    hazard_counts = {}

    for name, pattern in hazard_patterns.items():

        hazard_counts[name] = int(
            searchable_text.str.contains(
                pattern,
                regex=True,
                na=False
            ).sum()
        )


    hazard_df = pd.DataFrame(
        {
            "Hazard": list(
                hazard_counts.keys()
            ),
            "Reports": list(
                hazard_counts.values()
            )
        }
    )

    hazard_df = hazard_df.sort_values(
        "Reports",
        ascending=False
    )


    # ========================================================
    # BARRIER FAILURE DETECTION
    # ========================================================

    barrier_patterns = {

        "Inadequate Isolation":
            r"isolation|lockout|tagout|loto|depressur",

        "Inadequate Fall Protection":
            r"no fall protection|without fall protection|not tied off|not connected|unguarded edge|unprotected edge",

        "Inadequate Exclusion Zone":
            r"exclusion zone|danger zone|stood beneath|under suspended|struck by",

        "Inadequate Gas Testing":
            r"gas testing|gas test|oxygen testing|atmospheric testing|not tested",

        "Inadequate Guarding":
            r"unguarded|guard removed|without guard|machine guarding",

        "Poor Traffic Control":
            r"traffic control|flagger|pedestrian|backed over|reversing",

        "Shoring / Excavation Failure":
            r"cave-in|trench collapse|without shoring|no shoring"
    }


    barrier_counts = {}

    for name, pattern in barrier_patterns.items():

        barrier_counts[name] = int(
            searchable_text.str.contains(
                pattern,
                regex=True,
                na=False
            ).sum()
        )


    barrier_df = pd.DataFrame(
        {
            "Barrier Failure": list(
                barrier_counts.keys()
            ),
            "Reports": list(
                barrier_counts.values()
            )
        }
    )

    barrier_df = barrier_df.sort_values(
        "Reports",
        ascending=False
    )


    # ========================================================
    # DISPLAY CONCEPT CHARTS
    # ========================================================

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            "**Top Safety Activities**"
        )

        st.bar_chart(
            activity_df.head(8).set_index(
                "Activity"
            )
        )

    with c2:

        st.write(
            "**Top Hazards**"
        )

        st.bar_chart(
            hazard_df.head(8).set_index(
                "Hazard"
            )
        )


    st.write(
        "**Potential Barrier Failures**"
    )

    st.bar_chart(
        barrier_df.head(8).set_index(
            "Barrier Failure"
        )
    )


    # ========================================================
    # PRECURSOR PATTERNS
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🔥 Recurring Precursor Patterns'
        '</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Patterns below are generated from recurring "
        "activity, hazard and barrier indicators in the "
        "prototype dataset."
    )


    # --------------------------------------------------------
    # Generate meaningful precursor combinations
    # --------------------------------------------------------

    precursor_patterns = [

        (
            "Maintenance",
            "Stored Energy",
            "Inadequate Isolation"
        ),

        (
            "Lifting",
            "Suspended Load",
            "Inadequate Exclusion Zone"
        ),

        (
            "Work at Height",
            "Fall",
            "Inadequate Fall Protection"
        ),

        (
            "Electrical Work",
            "Electrical Energy",
            "Inadequate Isolation"
        ),

        (
            "Confined Space",
            "Toxic Atmosphere",
            "Inadequate Gas Testing"
        ),

        (
            "Driving / Vehicle",
            "Moving Equipment",
            "Poor Traffic Control"
        ),

        (
            "Excavation",
            "Caught-in / Pinch",
            "Shoring / Excavation Failure"
        )
    ]


    precursor_rows = []


    for activity, hazard, barrier in precursor_patterns:

        activity_count = activity_counts.get(
            activity,
            0
        )

        hazard_count = hazard_counts.get(
            hazard,
            0
        )

        barrier_count = barrier_counts.get(
            barrier,
            0
        )


        # Conservative pattern score.
        # Minimum component count prevents one
        # category from dominating the pattern.

        pattern_score = min(
            activity_count,
            hazard_count,
            barrier_count
        )


        precursor_rows.append(
            {
                "Activity": activity,
                "Hazard": hazard,
                "Barrier Failure": barrier,
                "Pattern Score": pattern_score
            }
        )


    precursor_df = pd.DataFrame(
        precursor_rows
    )

    precursor_df = precursor_df.sort_values(
        "Pattern Score",
        ascending=False
    )


    # ========================================================
    # SHOW PRECURSOR CARDS
    # ========================================================

    for index, row in precursor_df.iterrows():

        score = int(
            row["Pattern Score"]
        )

        if score > 100:

            priority = "HIGH"

        elif score > 30:

            priority = "MEDIUM"

        else:

            priority = "WATCH"


        st.write(
            f"### {priority} — "
            f"{row['Activity']} → "
            f"{row['Hazard']}"
        )

        st.write(
            f"**Barrier Failure:** "
            f"{row['Barrier Failure']}"
        )

        st.progress(
            min(
                score / max(
                    int(
                        precursor_df[
                            "Pattern Score"
                        ].max()
                    ),
                    1
                ),
                1.0
            )
        )

        st.caption(
            f"Pattern score: {score}"
        )


    # ========================================================
    # HSE INSIGHT
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '💡 HSE Intelligence'
        '</div>',
        unsafe_allow_html=True
    )


    top_activity = activity_df.iloc[0]

    top_hazard = hazard_df.iloc[0]

    top_barrier = barrier_df.iloc[0]


    st.info(
        f"""
        **Priority signal from the prototype dataset**

        • Most frequent activity indicator: **{top_activity['Activity']}**

        • Most frequent hazard indicator: **{top_hazard['Hazard']}**

        • Most frequent potential barrier failure: **{top_barrier['Barrier Failure']}**

        These signals can help HSE teams prioritize further
        investigation and intervention.
        """
    )


    st.caption(
        "Prototype only: these frequency-based insights "
        "are not official OIL safety statistics."
    )
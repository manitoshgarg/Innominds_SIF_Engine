from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
import re
from pathlib import Path

import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)


# ============================================================
# EXISTING AI MODULES
# ============================================================

from pipeline import analyze_report
from rule_mapper import map_life_saving_rule


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="INNOMINDS SIF Intelligence API",
    description=(
        "Backend API for SIF potential analysis, "
        "Life-Saving Rule mapping and precursor dashboard analytics"
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ReportRequest(BaseModel):
    report_text: str


# ============================================================
# DATA PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "osha_4470_prepared.csv"
)


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "message": "INNOMINDS SIF Intelligence API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# REPORT ANALYSIS
# ============================================================

@app.post("/analyze")
def analyze(request: ReportRequest):

    report_text = request.report_text.strip()

    if not report_text:
        return {
            "status": "error",
            "message": "Report text cannot be empty"
        }

    # Existing AI pipeline
    result = analyze_report(report_text)

    # Existing Life-Saving Rule mapper
    rules = map_life_saving_rule(report_text)

    return {
        "status": "success",
        "report_text": report_text,
        "sif_analysis": result,
        "life_saving_rules": rules
    }


# ============================================================
# DASHBOARD HELPERS
# ============================================================

def classify_concept(text, patterns, default="Other"):

    text = str(text).lower()

    for name, pattern in patterns.items():

        if re.search(pattern, text):
            return name

    return default


def add_dashboard_categories(df):

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    activity_patterns = {

        "Safe Mechanical Lifting":
            r"\b(crane|hoist|lifting|rigging|suspended load)\b",

        "Working at Height":
            r"\b(height|elevated|scaffold|ladder|roof|platform)\b",

        "Confined Space":
            r"\b(confined space|tank|vessel|manhole)\b",

        "Hot Work":
            r"\b(welding|cutting|grinding|hot work)\b",

        "Electrical Work":
            r"\b(electrical|energized|electrician|voltage|kV)\b",

        "Driving / Vehicle Operation":
            r"\b(forklift|vehicle|truck|driving|reversing|loader)\b",

        "Maintenance":
            r"\b(maintenance|repair|servicing|equipment)\b",
    }


    # --------------------------------------------------------
    # HAZARD
    # --------------------------------------------------------

    hazard_patterns = {

        "Fall From Height":
            r"\b(fall|fell|height|elevated|unprotected edge)\b",

        "Suspended Load":
            r"\b(suspended load|crane|hoist|lifting|rigging)\b",

        "Stored Energy":
            r"\b(pressure|residual pressure|stored energy|isolation)\b",

        "Electrical Energy":
            r"\b(energized|electrical|voltage|electric shock|kV)\b",

        "Fire / Explosion":
            r"\b(fire|explosion|flammable|hydrocarbon|vapour|vapor|ignition)\b",

        "Toxic Atmosphere":
            r"\b(oxygen|toxic|gas|atmosphere|confined space|ventilation)\b",

        "Moving Equipment":
            r"\b(forklift|vehicle|truck|loader|moving equipment|reversing)\b",
    }


    # --------------------------------------------------------
    # BARRIER FAILURE
    # --------------------------------------------------------

    barrier_patterns = {

        "Inadequate Isolation":
            r"\b(not isolated|not properly isolated|isolation.*not|residual pressure)\b",

        "Isolation Not Verified":
            r"\b(isolation.*not verified|not verified.*isolation)\b",

        "Inadequate Exclusion Zone":
            r"\b(exclusion zone|entered.*zone|beneath.*load|no.*exclusion)\b",

        "Inadequate Fall Protection":
            r"\b(fall protection|not connected|not wearing|unprotected edge)\b",

        "Inadequate Gas Testing":
            r"\b(gas test|gas testing|atmospheric testing|not.*tested|gas.*not)\b",

        "Inadequate Permit Control":
            r"\b(permit|work authorization|work authorisation)\b",

        "Inadequate Communication":
            r"\b(poor communication|limited visibility|communication failure)\b",
    }


    # --------------------------------------------------------
    # IOGP LIFE-SAVING RULE
    # --------------------------------------------------------

    rule_patterns = {

        "Energy Isolation":
            r"\b(isolation|isolated|residual pressure|stored energy|zero energy)\b",

        "Safe Mechanical Lifting":
            r"\b(crane|hoist|lifting|rigging|suspended load)\b",

        "Working at Height":
            r"\b(height|fall protection|elevated|scaffold|ladder|unprotected edge)\b",

        "Confined Space":
            r"\b(confined space|tank|vessel|manhole|oxygen|atmosphere)\b",

        "Hot Work":
            r"\b(welding|cutting|grinding|hot work|flammable vapour|flammable vapor)\b",

        "Driving":
            r"\b(forklift|vehicle|truck|driving|reversing|backing)\b",

        "Line of Fire":
            r"\b(line of fire|moving object|suspended load|exclusion zone|struck by)\b",

        "Bypassing Safety Controls":
            r"\b(bypass|bypassed|safety control|interlock)\b",

        "Work Authorisation":
            r"\b(work authorization|work authorisation|permit to work)\b",
    }


    # --------------------------------------------------------
    # REPORT TEXT
    # --------------------------------------------------------

    if "report_text" not in df.columns:

        # Safety fallback for dataset versions
        text_columns = [
            "title",
            "Summary2",
            "cause",
            "newkeys"
        ]

        available = [
            col for col in text_columns
            if col in df.columns
        ]

        if available:

            df["report_text"] = (
                df[available]
                .fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
            )

        else:

            df["report_text"] = ""


    # --------------------------------------------------------
    # CREATE CATEGORIES
    # --------------------------------------------------------

    df["activity"] = df["report_text"].apply(
        lambda x: classify_concept(
            x,
            activity_patterns
        )
    )

    df["hazard"] = df["report_text"].apply(
        lambda x: classify_concept(
            x,
            hazard_patterns
        )
    )

    df["barrier_failure"] = df["report_text"].apply(
        lambda x: classify_concept(
            x,
            barrier_patterns
        )
    )

    df["life_saving_rule"] = df["report_text"].apply(
        lambda x: classify_concept(
            x,
            rule_patterns
        )
    )

    return df


# ============================================================
# TOP VALUES
# ============================================================

def get_top_values(df, column, n=5):

    if column not in df.columns:
        return []

    values = (
        df[column]
        .fillna("Other")
        .value_counts()
        .head(n)
    )

    return [
        {
            "name": str(name),
            "count": int(count)
        }
        for name, count in values.items()
    ]


# ============================================================
# DASHBOARD ENDPOINT
# ============================================================

@app.get("/dashboard")
def dashboard():

    # --------------------------------------------------------
    # CHECK DATASET
    # --------------------------------------------------------

    if not DATA_FILE.exists():

        return {
            "status": "error",
            "message": f"Dataset not found: {DATA_FILE}"
        }


    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    df = pd.read_csv(DATA_FILE)


    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    total_reports = len(df)

    if "sif_label" in df.columns:

        sif_potential = int(
            (df["sif_label"] == 1).sum()
        )

    else:

        sif_potential = 0


    non_sif = total_reports - sif_potential


    # --------------------------------------------------------
    # DERIVE DASHBOARD CONCEPTS
    # --------------------------------------------------------

    df = add_dashboard_categories(df)


    # --------------------------------------------------------
    # HIGH PRIORITY
    #
    # Prototype approximation:
    # SIF-potential reports are treated as high-priority
    # for dashboard prioritization.
    # --------------------------------------------------------

    high_priority = sif_potential


    # --------------------------------------------------------
    # RECURRING PRECURSOR PATTERNS
    # --------------------------------------------------------

    precursor_df = (

        df[
            [
                "activity",
                "hazard",
                "barrier_failure"
            ]
        ]

        .fillna("Other")

        .groupby(
            [
                "activity",
                "hazard",
                "barrier_failure"
            ]
        )

        .size()

        .reset_index(
            name="count"
        )

        .sort_values(
            "count",
            ascending=False
        )

        .head(10)
    )


    recurring_precursors = [

        {
            "activity": str(row["activity"]),
            "hazard": str(row["hazard"]),
            "barrier_failure": str(row["barrier_failure"]),
            "count": int(row["count"])
        }

        for _, row in precursor_df.iterrows()
    ]


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "success",

        "total_reports": total_reports,

        "sif_potential": sif_potential,

        "non_sif": non_sif,

        "high_priority": high_priority,


        "sif_vs_non_sif": [

            {
                "name": "SIF-Potential",
                "count": sif_potential
            },

            {
                "name": "Non-SIF",
                "count": non_sif
            }

        ],


        "top_activities":
            get_top_values(
                df,
                "activity"
            ),


        "top_hazards":
            get_top_values(
                df,
                "hazard"
            ),


        "top_barriers":
            get_top_values(
                df,
                "barrier_failure"
            ),


        "top_life_saving_rules":
            get_top_values(
                df,
                "life_saving_rule"
            ),


        "recurring_precursors":
            recurring_precursors,


        "insight": (
            "Recurring precursor patterns are identified "
            "by aggregating activity, hazard and barrier "
            "failure signals from safety narratives."
        ),


        "disclaimer": (
            "Prototype analytics based on public OSHA "
            "safety data and development labels — not "
            "OIL SIF prevalence estimates."
        )
    }
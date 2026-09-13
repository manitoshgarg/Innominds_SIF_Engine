import pandas as pd
import os
import re


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

INPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "osha_4470.xlsx"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "osha_4470_prepared.csv"
)


# ============================================================
# SIF RISK INDICATORS
# ============================================================

HIGH_RISK_PATTERNS = {

    "fatality": [
        r"\bkilled\b",
        r"\bdied\b",
        r"\bdead\b",
        r"\bdeath\b",
        r"\bfatal\b",
        r"\bpronounced dead\b"
    ],

    "fall_from_height": [
        r"\bfall from\b",
        r"\bfalling from\b",
        r"\bfall from height\b",
        r"\bfallen from\b",
        r"\bhigh elevation\b",
        r"\broof\b",
        r"\bscaffold\b"
    ],

    "struck_by": [
        r"\bstruck by\b",
        r"\bhit by\b",
        r"\bstruck\b",
        r"\bvehicle\b",
        r"\bmotor vehicle\b"
    ],

    "caught_between": [
        r"\bcaught between\b",
        r"\bcaught in\b",
        r"\bcrushed\b",
        r"\bpinning\b",
        r"\bpinned\b",
        r"\btrapped\b"
    ],

    "electrical": [
        r"\belectroc",
        r"\belectrical\b",
        r"\belectric shock\b",
        r"\benergized\b",
        r"\bhigh voltage\b"
    ],

    "fire_explosion": [
        r"\bexplosion\b",
        r"\bexploded\b",
        r"\bfire\b",
        r"\bflammable\b",
        r"\bignition\b"
    ],

    "confined_space": [
        r"\bconfined space\b",
        r"\btank\b",
        r"\bvessel\b",
        r"\bmanhole\b",
        r"\btoxic gas\b",
        r"\black of oxygen\b",
        r"\boxygen deficiency\b"
    ],

    "lifting": [
        r"\bsuspended load\b",
        r"\blifting\b",
        r"\bcrane\b",
        r"\bhoist\b",
        r"\bforklift\b",
        r"\boverhead load\b"
    ],

    "energy_release": [
        r"\bpressure\b",
        r"\bpressurized\b",
        r"\bresidual pressure\b",
        r"\bstored energy\b",
        r"\benergy release\b",
        r"\bunexpected movement\b"
    ],

    "amputation": [
        r"\bamputat",
        r"\bsevered\b",
        r"\bamputation\b"
    ]
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Convert a value to clean lowercase text."""

    if pd.isna(value):
        return ""

    text = str(value)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()


def detect_indicators(text):
    """
    Detect high-risk safety indicators in a report.
    Returns indicator names and a score.
    """

    detected = []

    for indicator, patterns in HIGH_RISK_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text, flags=re.IGNORECASE):

                detected.append(indicator)

                break

    return detected


def calculate_weak_sif_label(indicators, text):
    """
    Create an initial expert-informed weak SIF label.

    IMPORTANT:
    These are development labels only.
    They are NOT official OIL SIF labels.
    """

    text = text.lower()

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 1. Fatal outcome
    # --------------------------------------------------------

    if "fatality" in indicators:
        score += 5
        reasons.append("fatal_outcome")

    # --------------------------------------------------------
    # 2. Very strong fatal-potential mechanisms
    # --------------------------------------------------------

    # Fall + significant height/elevation
    if "fall_from_height" in indicators:

        height_evidence = [
            r"\b\d+\s*(?:ft|feet|foot)\b",
            r"\bstory\b",
            r"\bstories\b",
            r"\bheight\b",
            r"\belevated\b",
            r"\bunprotected edge\b"
        ]

        if any(re.search(pattern, text) for pattern in height_evidence):
            score += 4
            reasons.append("fall_with_height_exposure")

    # --------------------------------------------------------
    # 3. Caught-between / crushing exposure
    # --------------------------------------------------------

    if "caught_between" in indicators:

        exposure_terms = [
            "pinned",
            "trapped",
            "crushed",
            "caught between",
            "caught in",
            "run over"
        ]

        if any(term in text for term in exposure_terms):
            score += 4
            reasons.append("caught_between_high_energy")

    # --------------------------------------------------------
    # 4. Electrical exposure
    # --------------------------------------------------------

    if "electrical" in indicators:

        electrical_exposure = [
            "energized",
            "live",
            "high voltage",
            "contact with",
            "electrocuted",
            "electrocution",
            "electric shock"
        ]

        if any(term in text for term in electrical_exposure):
            score += 4
            reasons.append("electrical_energy_exposure")

    # --------------------------------------------------------
    # 5. Fire / explosion
    # --------------------------------------------------------

    if "fire_explosion" in indicators:

        severe_fire_terms = [
            "explosion",
            "exploded",
            "flash fire",
            "fireball",
            "ignition",
            "flammable vapor"
        ]

        if any(term in text for term in severe_fire_terms):
            score += 4
            reasons.append("fire_explosion_energy")

    # --------------------------------------------------------
    # 6. Confined-space exposure
    # --------------------------------------------------------

    if "confined_space" in indicators:

        atmospheric_terms = [
            "toxic gas",
            "hydrogen sulfide",
            "h2s",
            "oxygen deficiency",
            "lack of oxygen",
            "unconscious",
            "overcome"
        ]

        if any(term in text for term in atmospheric_terms):
            score += 4
            reasons.append("confined_space_atmospheric_hazard")

    # --------------------------------------------------------
    # 7. Lifting / suspended load
    # --------------------------------------------------------

    if "lifting" in indicators:

        lifting_exposure = [
            "suspended load",
            "load fell",
            "load struck",
            "crane load",
            "crane struck",
            "crushed by",
            "pinned"
        ]

        if any(term in text for term in lifting_exposure):
            score += 4
            reasons.append("lifting_high_energy_exposure")

    # --------------------------------------------------------
    # 8. Stored / released energy
    # --------------------------------------------------------

    if "energy_release" in indicators:

        energy_terms = [
            "residual pressure",
            "pressurized",
            "pressure release",
            "unexpected release",
            "stored energy",
            "unexpected movement",
            "energized"
        ]

        if any(term in text for term in energy_terms):
            score += 4
            reasons.append("uncontrolled_energy_release")

    # --------------------------------------------------------
    # 9. Vehicle / struck-by exposure
    # --------------------------------------------------------

    if "struck_by" in indicators:

        vehicle_exposure = [
            "worker struck",
            "employee struck",
            "person struck",
            "vehicle struck",
            "run over",
            "backed over",
            "vehicle hit"
        ]

        if any(term in text for term in vehicle_exposure):
            score += 4
            reasons.append("struck_by_vehicle_exposure")

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    if score >= 4:

        return 1, "; ".join(reasons)

    return 0, "no_strong_sif_evidence"


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("INNOMINDS - REAL DATASET PREPARATION")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_excel(INPUT_PATH)

print(f"Loaded {len(df)} reports.")


# ============================================================
# REMOVE UNNECESSARY COLUMN
# ============================================================

if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

print("\nRemoved unnecessary Excel index column.")


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "id",
    "title",
    "Summary2",
    "cause",
    "newkeys"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("\nERROR: Missing columns:")
    print(missing_columns)

    raise ValueError(
        "The dataset does not contain the expected columns."
    )


# ============================================================
# CLEAN TEXT COLUMNS
# ============================================================

print("\nCleaning text...")

for column in ["title", "Summary2", "cause", "newkeys"]:

    df[column] = df[column].apply(clean_text)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=["Summary2"],
    keep="first"
)

after_duplicates = len(df)

print(
    f"Removed duplicate reports: "
    f"{before_duplicates - after_duplicates}"
)


# ============================================================
# CREATE COMBINED TEXT
# ============================================================

print("\nCreating combined report text...")

df["report_text"] = (
    df["title"] + " " +
    df["Summary2"] + " " +
    df["cause"] + " " +
    df["newkeys"]
).str.strip()


# ============================================================
# TEXT LENGTH
# ============================================================

df["text_length"] = df["report_text"].str.len()


# ============================================================
# DETECT SAFETY INDICATORS
# ============================================================

print("\nDetecting safety-risk indicators...")

df["sif_indicators"] = df["report_text"].apply(
    detect_indicators
)

df["indicator_count"] = df["sif_indicators"].apply(
    len
)


# ============================================================
# CREATE INITIAL WEAK LABEL
# ============================================================

print("\nCreating initial weak SIF labels...")

label_results = df.apply(
    lambda row: calculate_weak_sif_label(
        row["sif_indicators"],
        row["report_text"]
    ),
    axis=1
)

df["sif_label"] = label_results.apply(
    lambda x: x[0]
)

df["label_reason"] = label_results.apply(
    lambda x: x[1]
)


# ============================================================
# HUMAN-READABLE INDICATORS
# ============================================================

df["sif_indicators"] = df["sif_indicators"].apply(
    lambda x: ", ".join(x)
)


# ============================================================
# SAVE PROCESSED DATASET
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DATASET PREPARATION COMPLETE")
print("=" * 70)

print("\nFinal reports :", len(df))

print("\nSIF label distribution:")

print(
    df["sif_label"]
    .value_counts()
    .sort_index()
)

print("\nLabel meanings:")

print("0 = Initial NON-SIF candidate")
print("1 = Initial SIF-POTENTIAL candidate")

print("\nLabel reasons:")

print(
    df["label_reason"]
    .value_counts()
)

print("\nAverage report length:")

print(
    round(df["text_length"].mean(), 2),
    "characters"
)

print("\nPrepared dataset saved to:")

print(OUTPUT_PATH)

print("\n" + "=" * 70)
print("IMPORTANT")
print("=" * 70)

print(
    "These are weak development labels, "
    "NOT official OIL SIF labels."
)

print(
    "They must be validated/refined before "
    "being used as final project labels."
)


# ============================================================
# SAMPLE LABEL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("SAMPLE LABEL VALIDATION")
print("=" * 70)

print("\nThe following examples are for manual validation.")
print("They are NOT official SIF labels.")


# ------------------------------------------------------------
# Positive examples
# ------------------------------------------------------------

positive_samples = df[df["sif_label"] == 1].sample(
    n=min(5, len(df[df["sif_label"] == 1])),
    random_state=42
)

print("\n" + "-" * 70)
print("SIF-POTENTIAL CANDIDATE EXAMPLES")
print("-" * 70)

for _, row in positive_samples.iterrows():

    print("\nREPORT ID:", row["id"])
    print("TITLE:", row["title"])
    print("INDICATORS:", row["sif_indicators"])
    print("REASON:", row["label_reason"])

    print("\nREPORT:")
    print(row["Summary2"][:1000])

    print("\n" + "-" * 70)


# ------------------------------------------------------------
# Negative examples
# ------------------------------------------------------------

negative_samples = df[df["sif_label"] == 0].sample(
    n=min(5, len(df[df["sif_label"] == 0])),
    random_state=42
)

print("\n" + "-" * 70)
print("NON-SIF CANDIDATE EXAMPLES")
print("-" * 70)

for _, row in negative_samples.iterrows():

    print("\nREPORT ID:", row["id"])
    print("TITLE:", row["title"])
    print("INDICATORS:", row["sif_indicators"])
    print("REASON:", row["label_reason"])

    print("\nREPORT:")
    print(row["Summary2"][:1000])

    print("\n" + "-" * 70)


    # ============================================================
# CREATE HUMAN REVIEW SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("CREATING HUMAN REVIEW SAMPLE")
print("=" * 70)

# Select reports from different automatically detected groups
fatal_reports = df[
    df["label_reason"].str.contains(
        "fatal_outcome",
        na=False
    )
]

risk_reports = df[
    df["indicator_count"] >= 1
]

low_reports = df[
    df["sif_label"] == 0
]

# Sample from each group
fatal_sample = fatal_reports.sample(
    n=min(40, len(fatal_reports)),
    random_state=42
)

risk_sample = risk_reports.sample(
    n=min(30, len(risk_reports)),
    random_state=43
)

low_sample = low_reports.sample(
    n=min(30, len(low_reports)),
    random_state=44
)

review_df = pd.concat(
    [
        fatal_sample,
        risk_sample,
        low_sample
    ]
).drop_duplicates(
    subset=["id"]
)

# Shuffle
review_df = review_df.sample(
    frac=1,
    random_state=45
).reset_index(drop=True)

# Add empty human-review columns
review_df["human_sif_label"] = ""
review_df["review_reason"] = ""

review_columns = [
    "id",
    "title",
    "Summary2",
    "cause",
    "newkeys",
    "sif_indicators",
    "label_reason",
    "human_sif_label",
    "review_reason"
]

review_df[review_columns].to_csv(
    os.path.join(
        OUTPUT_DIR,
        "sif_review_sample.csv"
    ),
    index=False
)

print(
    "\nHuman review file created:"
)

print(
    os.path.join(
        OUTPUT_DIR,
        "sif_review_sample.csv"
    )
)

print(
    "\nReview sample size:",
    len(review_df)
)


# ============================================================
# CREATE AMBIGUOUS HUMAN REVIEW SET
# ============================================================

print("\n" + "=" * 70)
print("CREATING AMBIGUOUS HUMAN REVIEW SET")
print("=" * 70)

# Reports that contain some safety indicators but do not have
# a very strong automatic SIF signal.
#
# These are the cases where human judgment is most useful.

ambiguous_reports = df[
    (
        (df["sif_label"] == 0) &
        (df["indicator_count"] > 0)
    )
    |
    (
        (df["sif_label"] == 1) &
        (~df["label_reason"].str.contains(
            "fatal_outcome",
            na=False
        )) &
        (df["indicator_count"] <= 2)
    )
].copy()


# ------------------------------------------------------------
# Select a manageable review sample
# ------------------------------------------------------------

review_count = min(50, len(ambiguous_reports))

ambiguous_review = ambiguous_reports.sample(
    n=review_count,
    random_state=100
).reset_index(drop=True)


# ------------------------------------------------------------
# Add human review columns
# ------------------------------------------------------------

ambiguous_review["human_sif_label"] = ""
ambiguous_review["review_reason"] = ""


# ------------------------------------------------------------
# Select useful columns
# ------------------------------------------------------------

review_columns = [
    "id",
    "title",
    "Summary2",
    "cause",
    "newkeys",
    "sif_indicators",
    "label_reason",
    "human_sif_label",
    "review_reason"
]


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

AMBIGUOUS_REVIEW_PATH = os.path.join(
    OUTPUT_DIR,
    "sif_ambiguous_review.csv"
)

ambiguous_review[review_columns].to_csv(
    AMBIGUOUS_REVIEW_PATH,
    index=False
)


print("\nAmbiguous review file created:")
print(AMBIGUOUS_REVIEW_PATH)

print("\nReports selected for human review:")
print(len(ambiguous_review))

print("\nThese reports require human validation.")
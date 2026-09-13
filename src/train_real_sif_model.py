import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix


# ============================================================
# V5 — REAL DATA SIF CLASSIFIER
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

os.makedirs(MODEL_DIR, exist_ok=True)


PREPARED_DATA = os.path.join(
    PROCESSED_DIR,
    "osha_4470_prepared.csv"
)

REVIEWED_DATA = os.path.join(
    PROCESSED_DIR,
    "sif_100_human_reviewed.csv"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "sif_tfidf_logreg.joblib"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("INNOMINDS — V5 REAL DATA SIF CLASSIFIER")
print("=" * 70)

print("\nLoading prepared OSHA dataset...")

df = pd.read_csv(
    PREPARED_DATA
)

print(
    f"Prepared reports loaded: {len(df)}"
)


print("\nLoading human-reviewed dataset...")

reviewed = pd.read_csv(
    REVIEWED_DATA
)

print(
    f"Reviewed reports loaded: {len(reviewed)}"
)


# ============================================================
# CLEAN REVIEWED LABELS
# ============================================================

reviewed["human_sif_label"] = (
    reviewed["human_sif_label"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Keep only SIF / NON-SIF
reviewed_valid = reviewed[
    reviewed["human_sif_label"].isin(
        ["SIF", "NON-SIF"]
    )
].copy()


# ============================================================
# PREPARE TEXT
# ============================================================

reviewed_valid["report_text"] = (
    reviewed_valid["title"].fillna("")
    + " "
    + reviewed_valid["Summary2"].fillna("")
    + " "
    + reviewed_valid["cause"].fillna("")
    + " "
    + reviewed_valid["newkeys"].fillna("")
)


# Convert labels:
# SIF     -> 1
# NON-SIF -> 0

reviewed_valid["label"] = (
    reviewed_valid["human_sif_label"]
    .map({
        "SIF": 1,
        "NON-SIF": 0
    })
)


# ============================================================
# REMOVE REVIEWED REPORTS FROM WEAK DATA
# ============================================================

reviewed_ids = set(
    reviewed_valid["id"].astype(str)
)

df["id"] = df["id"].astype(str)


weak_train = df[
    ~df["id"].isin(reviewed_ids)
].copy()


# ============================================================
# PREPARE WEAK DATA
# ============================================================

weak_train["report_text"] = (
    weak_train["report_text"]
    .fillna("")
    .astype(str)
)

weak_train["label"] = (
    weak_train["sif_label"]
    .astype(int)
)


# ============================================================
# COMBINE DATA
# ============================================================

review_train = reviewed_valid[
    ["report_text", "label"]
].copy()

weak_train = weak_train[
    ["report_text", "label"]
].copy()


# Use real reviewed labels multiple times so they
# have stronger influence than weak labels.

review_train_boosted = pd.concat(
    [review_train] * 3,
    ignore_index=True
)


training_data = pd.concat(
    [
        weak_train,
        review_train_boosted
    ],
    ignore_index=True
)


training_data = training_data[
    training_data["report_text"].str.strip() != ""
]


print("\nTraining data:")
print(
    f"Weak reports       : {len(weak_train)}"
)

print(
    f"Reviewed reports   : {len(review_train)}"
)

print(
    f"Final training rows: {len(training_data)}"
)

print("\nTraining label distribution:")

print(
    training_data["label"]
    .value_counts()
    .sort_index()
)


# ============================================================
# BUILD MODEL
# ============================================================

print("\nBuilding TF-IDF + Logistic Regression model...")

model = Pipeline(
    [
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True
            )
        ),

        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced"
            )
        )
    ]
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining model...")

model.fit(
    training_data["report_text"],
    training_data["label"]
)

print("Training completed.")


# ============================================================
# EVALUATE ONLY ON HUMAN-REVIEWED DATA
# ============================================================

print("\n" + "=" * 70)
print("EVALUATION ON HUMAN-REVIEWED REPORTS")
print("=" * 70)

X_test = reviewed_valid["report_text"]
y_test = reviewed_valid["label"]


predictions = model.predict(
    X_test
)


print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        target_names=[
            "NON-SIF",
            "SIF"
        ],
        zero_division=0
    )
)


print("Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        predictions
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    MODEL_PATH
)

print("\n" + "=" * 70)

print(
    "MODEL SAVED SUCCESSFULLY"
)

print(
    MODEL_PATH
)

print("=" * 70)
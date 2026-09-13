"""
INNOMINDS SIH 2026 - Baseline SIF classifier
This is a development/demo baseline using synthetic data.
Do not describe the demo dataset as OIL proprietary data.
"""

from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "safety_reports_demo.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA)

X_train, X_test, y_train, y_test = train_test_split(
    df["report_text"],
    df["sif_label"],
    test_size=0.25,
    random_state=42,
    stratify=df["sif_label"],
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95
    )),
    ("classifier", LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    )),
])

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("\n=== Classification Report ===")
print(classification_report(
    y_test, pred,
    target_names=["Non-SIF", "SIF-Potential"],
    digits=3
))

print("=== Confusion Matrix ===")
print(confusion_matrix(y_test, pred))

model_path = MODEL_DIR / "sif_tfidf_logreg.joblib"
joblib.dump(model, model_path)
print(f"\nSaved model to: {model_path}")

examples = [
    "Worker entered a confined space without atmospheric testing.",
    "Worker wore required PPE during routine inspection.",
    "A valve was opened without confirming energy isolation.",
]

print("\n=== Demo Predictions ===")
for text in examples:
    label = int(model.predict([text])[0])
    probability = float(model.predict_proba([text])[0].max())
    name = "SIF-Potential" if label == 1 else "Non-SIF"
    print(f"{name:15} | {probability:.3f} | {text}")

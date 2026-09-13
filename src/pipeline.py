import os
import joblib

from structured_event_extractor import extract_structured_events


# ============================================================
# V3.6 - UNIFIED SAFETY ANALYSIS PIPELINE
# ============================================================


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "sif_tfidf_logreg.joblib"
)


# ------------------------------------------------------------
# Load SIF classifier
# ------------------------------------------------------------

print("Loading SIF classifier...")

sif_model = joblib.load(MODEL_PATH)

print("SIF classifier loaded.")


# ------------------------------------------------------------
# SIF classification
# ------------------------------------------------------------

def classify_sif(report_text):

    prediction = sif_model.predict(
        [report_text]
    )[0]

    probabilities = sif_model.predict_proba(
        [report_text]
    )[0]

    classes = sif_model.classes_

    probability_map = {
        str(cls): float(prob)
        for cls, prob in zip(
            classes,
            probabilities
        )
    }

    confidence = float(
        max(probabilities)
    )

    # Convert model output into readable label
    if str(prediction) == "1":
        sif_label = "SIF-POTENTIAL"
    else:
        sif_label = "NON-SIF-POTENTIAL"

    return {
        "label": sif_label,
        "confidence": confidence,
        "probabilities": probability_map
    }


# ------------------------------------------------------------
# Analyze complete report
# ------------------------------------------------------------

def analyze_report(report_text):

    if not report_text or not report_text.strip():

        raise ValueError(
            "Report text cannot be empty."
        )

    # --------------------------------------------
    # 1. SIF Classification
    # --------------------------------------------

    sif_result = classify_sif(
        report_text
    )

    # --------------------------------------------
    # 2. Structured Event Extraction
    # --------------------------------------------

    events = extract_structured_events(
        report_text
    )

    # --------------------------------------------
    # Final result
    # --------------------------------------------

    result = {

        "sif_classification": sif_result,

        "event_count": len(events),

        "events": events
    }

    return result


# ------------------------------------------------------------
# Display final result
# ------------------------------------------------------------

def print_pipeline_result(result):

    print("\n")
    print("=" * 80)
    print("INNOMINDS - SAFETY INTELLIGENCE PIPELINE")
    print("=" * 80)

    sif = result["sif_classification"]

    print("\nSIF CLASSIFICATION")
    print("-" * 80)

    print(
        f"Result     : {sif['label']}"
    )

    print(
        f"Confidence : {sif['confidence']:.3f}"
    )

    print("\nEVENT ANALYSIS")
    print("-" * 80)

    print(
        f"Events detected: "
        f"{result['event_count']}"
    )

    for event in result["events"]:

        print("\n" + "-" * 60)

        print(
            f"Event ID        : "
            f"E{event['event_id']}"
        )

        print(
            f"Activity        : "
            f"{event['activity']}"
        )

        print(
            f"Hazard          : "
            f"{event['hazard']}"
        )

        print(
            f"Barrier Failure : "
            f"{event['barrier_failure']}"
        )

        print(
            f"Consequence     : "
            f"{event['consequence']}"
        )

        print(
            f"Relevance       : "
            f"{event['relevance']:.3f}"
        )

        print("\nEvidence:")

        for sentence in event["evidence"]:

            print(
                f"  • {sentence}"
            )

    print("\n")
    print("=" * 80)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    report = """
    During maintenance of a compressor, the equipment was shut down.
    The isolation valve was closed but the isolation was not verified.
    Residual pressure remained inside the process line.
    Two workers started removing the flange while standing close to the line.
    The supervisor noticed the unsafe condition and immediately stopped the work.
    The permit was reviewed and the isolation was verified before work resumed.
    """

    result = analyze_report(
        report
    )

    print_pipeline_result(
        result
    )
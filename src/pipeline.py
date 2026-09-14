import os
import re
import joblib

from structured_event_extractor import extract_structured_events


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "sif_tfidf_logreg.joblib"
)

print("Loading SIF classifier...")
sif_model = joblib.load(MODEL_PATH)
print("SIF classifier loaded.")


# ============================================================
# SAFETY INDICATOR ENGINE
# ============================================================

def detect_sif_indicators(report_text):
    """
    Detect strong high-energy safety scenarios from free text.

    These indicators are used as a safety triage layer alongside
    the machine-learning classifier.

    This is prototype domain logic, not an official OIL SIF rule set.
    """

    text = report_text.lower()

    indicators = []

    # --------------------------------------------------------
    # 1. FALL FROM HEIGHT
    # --------------------------------------------------------

    height_context = re.search(
        r"(fall|fell|falling|height|elevated|platform|roof|scaffold|tower|edge|ladder)",
        text
    )

    height_evidence = re.search(
        r"(\d+\s*(ft|feet|foot|metre|meter|m))"
        r"|(\d+\s*[-]?\s*(story|stories))"
        r"|(unprotected\s+edge)"
        r"|(fall\s+protection)"
        r"|(not\s+(?:connected|attached|tied))",
        text
    )

    # Avoid treating phrases such as "no fall" as a positive fall event.
    explicit_no_fall = re.search(
        r"\b(no|without)\s+(actual\s+)?fall\b",
        text
    )

    if height_context and height_evidence and not explicit_no_fall:
        indicators.append({
            "type": "Fall From Height",
            "severity": "HIGH",
            "reason": "Fall/height exposure with significant fall-risk evidence."
        })


    # --------------------------------------------------------
    # 2. ELECTRICAL ENERGY
    # --------------------------------------------------------

    electrical = re.search(
        r"(energized|live|high\s*voltage|kV|electrical\s+line|"
        r"power\s+line|electrocution|energised)",
        text
    )

    electrical_exposure = re.search(
        r"(worker|electrician|personnel|employee).{0,100}"
        r"(near|within|contact|came\s+within|working\s+near|exposed)",
        text
    )

    electrical_isolation_failure = re.search(
        r"(not\s+properly\s+isolated|not\s+isolated|"
        r"not\s+de[-\s]?energized|not\s+deenergized)",
        text
    )

    if electrical and (electrical_exposure or electrical_isolation_failure):
        indicators.append({
            "type": "Energized Electrical Exposure",
            "severity": "HIGH",
            "reason": "Personnel exposed to energized electrical equipment or conductors."
        })


    # --------------------------------------------------------
    # 3. STORED ENERGY / PRESSURE / ISOLATION
    # --------------------------------------------------------

    isolation_failure = re.search(
        r"(isolation\s+(was\s+)?not\s+verified|"
        r"isolation\s+not\s+verified|"
        r"not\s+properly\s+isolated|"
        r"lockout.{0,30}(not|missing|failed)|"
        r"LOTO.{0,30}(not|missing|failed)|"
        r"zero\s+energy\s+(was\s+)?not\s+verified)",
        text
    )

    stored_energy = re.search(
        r"(residual\s+pressure|"
        r"stored\s+energy|"
        r"trapped\s+pressure|"
        r"pressurized|"
        r"pressure\s+remained|"
        r"uncontrolled\s+energy|"
        r"unexpected\s+release|"
        r"released\s+pressure|"
        r"depressurization\s+failure)",
        text
    )

    maintenance_context = re.search(
        r"(maintenance|repair|servicing|flange|valve|process\s+line|"
        r"equipment|compressor|pump|pipeline)",
        text
    )

    if (isolation_failure and stored_energy) or (
        isolation_failure and maintenance_context
    ):
        indicators.append({
            "type": "Uncontrolled Stored Energy",
            "severity": "HIGH",
            "reason": "Energy isolation/verification failure creates potential for uncontrolled release."
        })


    # --------------------------------------------------------
    # 4. SUSPENDED LOAD / LIFTING
    # --------------------------------------------------------

    suspended_load = re.search(
        r"(suspended\s+load|"
        r"load\s+was\s+suspended|"
        r"hanging\s+load|"
        r"crane|hoist|lifting|rigging)",
        text
    )

    person_exposure = re.search(
        r"(worker|person|employee|personnel).{0,100}"
        r"(beneath|under|below|exclusion\s+zone|danger\s+zone|"
        r"struck|hit|toward|entered)",
        text
    )

    if suspended_load and person_exposure:
        indicators.append({
            "type": "Suspended Load / Line of Fire",
            "severity": "HIGH",
            "reason": "Person entered or was exposed to the path of a suspended or moving load."
        })


    # --------------------------------------------------------
    # 5. CONFINED SPACE
    # --------------------------------------------------------

    confined_space = re.search(
        r"(confined\s+space|storage\s+tank|tank|vessel|manhole|"
        r"inside\s+the\s+tank|confined\s+area)",
        text
    )

    atmosphere_hazard = re.search(
        r"(oxygen|oxygen\s+level|oxygen\s+deficien|"
        r"toxic\s+gas|toxic\s+atmosphere|"
        r"hazardous\s+atmosphere|"
        r"gas\s+testing|atmospheric\s+testing|"
        r"flammable\s+gas|inadequate\s+ventilation)",
        text
    )

    if confined_space and atmosphere_hazard:
        indicators.append({
            "type": "Confined Space Atmospheric Hazard",
            "severity": "HIGH",
            "reason": "Confined-space entry combined with atmospheric or ventilation hazard."
        })


    # --------------------------------------------------------
    # 6. FIRE / EXPLOSION / HOT WORK
    # --------------------------------------------------------

    hot_work = re.search(
        r"(hot\s+work|welding|welder|cutting|grinding|"
        r"spark|ignition|torch)",
        text
    )

    flammable_context = re.search(
        r"(hydrocarbon|flammable|vapou?r|gas|fuel|"
        r"combustible|explosive|process\s+line)",
        text
    )

    if hot_work and flammable_context:
        indicators.append({
            "type": "Fire / Explosion Potential",
            "severity": "HIGH",
            "reason": "Hot work or ignition source is combined with a flammable atmosphere/material."
        })


    # --------------------------------------------------------
    # 7. VEHICLE / PEDESTRIAN
    # --------------------------------------------------------

    vehicle = re.search(
        r"(forklift|vehicle|truck|car|loader|crane|"
        r"mobile\s+equipment|reversing|backing)",
        text
    )

    pedestrian_exposure = re.search(
        r"(pedestrian|worker|person|employee).{0,100}"
        r"(near|toward|path|area|struck|run\s*over|"
        r"exclusion\s+zone|limited\s+visibility)",
        text
    )

    if vehicle and pedestrian_exposure:
        indicators.append({
            "type": "Vehicle-Pedestrian Interaction",
            "severity": "HIGH",
            "reason": "Worker exposure to moving vehicle/mobile equipment."
        })


    # --------------------------------------------------------
    # 8. CAUGHT BETWEEN / CRUSHING
    # --------------------------------------------------------

    caught_between = re.search(
        r"(caught\s+between|"
        r"pinned|"
        r"crushed|"
        r"trapped|"
        r"entangled|"
        r"caught\s+in)",
        text
    )

    moving_equipment = re.search(
        r"(machinery|machine|equipment|vehicle|"
        r"moving\s+equipment|rotating|conveyor|"
        r"mechanical)",
        text
    )

    if caught_between and moving_equipment:
        indicators.append({
            "type": "Caught Between / Crushing",
            "severity": "HIGH",
            "reason": "Potential caught-between or crushing exposure involving equipment or machinery."
        })


    # --------------------------------------------------------
    # 9. EXCAVATION / TRENCH
    # --------------------------------------------------------

    excavation = re.search(
        r"(trench|excavation|excavated|ditch)",
        text
    )

    collapse = re.search(
        r"(collapse|cave[-\s]?in|caved\s+in|"
        r"shoring\s+(was\s+)?not|"
        r"unshored|unstable\s+wall)",
        text
    )

    if excavation and collapse:
        indicators.append({
            "type": "Excavation Collapse",
            "severity": "HIGH",
            "reason": "Excavation/trench instability creates potential for burial or crushing."
        })


    return indicators


# ============================================================
# SIF CLASSIFIER
# ============================================================

def classify_sif(report_text):

    if not report_text or not report_text.strip():
        raise ValueError("Report text cannot be empty.")

    # -----------------------------
    # Machine-learning prediction
    # -----------------------------

    prediction = sif_model.predict([report_text])[0]

    probabilities = sif_model.predict_proba([report_text])[0]

    classes = sif_model.classes_

    probability_map = {
        str(cls): float(prob)
        for cls, prob in zip(classes, probabilities)
    }

    ml_score = float(probability_map.get("1", 0.0))

    ml_label = (
        "SIF-POTENTIAL"
        if str(prediction) == "1"
        else "NON-SIF-POTENTIAL"
    )

    # -----------------------------
    # Safety indicator layer
    # -----------------------------

    indicators = detect_sif_indicators(report_text)

    # -----------------------------
    # Final hybrid decision
    # -----------------------------

    if len(indicators) > 0:
        final_label = "SIF-POTENTIAL"
        priority = "HIGH"
        override_applied = True

    elif ml_score >= 0.50:
        final_label = "SIF-POTENTIAL"
        priority = "MEDIUM"
        override_applied = False

    else:
        final_label = "NON-SIF-POTENTIAL"
        priority = "LOW"
        override_applied = False

    # -----------------------------
    # Safety score
    # -----------------------------

    if indicators:
        # Keep ML score visible, but make the final triage score
        # reflect the presence of strong safety indicators.
        safety_score = max(ml_score, 0.85)
    else:
        safety_score = ml_score

    # -----------------------------
    # Explainable reasons
    # -----------------------------

    reasons = [
        indicator["reason"]
        for indicator in indicators
    ]

    return {
        "label": final_label,

        # Existing key retained so the current dashboard
        # continues to work.
        "confidence": safety_score,

        # More accurate terminology for the UI.
        "ml_score": ml_score,

        "safety_score": safety_score,

        "priority": priority,

        "ml_label": ml_label,

        "override_applied": override_applied,

        "indicators": indicators,

        "reasons": reasons,

        "probabilities": probability_map
    }


# ============================================================
# COMPLETE REPORT ANALYSIS
# ============================================================

def analyze_report(report_text):

    if not report_text or not report_text.strip():
        raise ValueError("Report text cannot be empty.")

    sif_result = classify_sif(report_text)

    events = extract_structured_events(report_text)

    return {
        "sif_classification": sif_result,
        "event_count": len(events),
        "events": events
    }


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def print_pipeline_result(result):

    print("\n")
    print("=" * 80)
    print("INNOMINDS - SAFETY INTELLIGENCE PIPELINE")
    print("=" * 80)

    sif = result["sif_classification"]

    print("\nSIF CLASSIFICATION")
    print("-" * 80)

    print(f"Final Result       : {sif['label']}")
    print(f"ML Score           : {sif['ml_score']:.3f}")
    print(f"Safety Score       : {sif['safety_score']:.3f}")
    print(f"HSE Priority       : {sif['priority']}")
    print(f"ML Result          : {sif['ml_label']}")
    print(f"Safety Override    : {sif['override_applied']}")

    if sif["indicators"]:

        print("\nSafety Indicators")
        print("-" * 80)

        for indicator in sif["indicators"]:
            print(
                f"  [HIGH] {indicator['type']} "
                f"- {indicator['reason']}"
            )

    print("\nEVENT ANALYSIS")
    print("-" * 80)

    print(f"Events detected: {result['event_count']}")

    for event in result["events"]:

        print("\n" + "-" * 60)

        print(f"Event ID        : E{event['event_id']}")
        print(f"Activity        : {event['activity']}")
        print(f"Hazard          : {event['hazard']}")
        print(f"Barrier Failure : {event['barrier_failure']}")
        print(f"Consequence     : {event['consequence']}")
        print(f"Relevance       : {event['relevance']:.3f}")

        print("\nEvidence:")

        for sentence in event["evidence"]:
            print(f"  • {sentence}")

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
    The unsafe condition was identified before any injury occurred and the work was stopped.
    """

    result = analyze_report(report)

    print_pipeline_result(result)
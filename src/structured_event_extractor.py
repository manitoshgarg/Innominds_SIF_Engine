from event_analyzer import analyze_events


# ============================================================
# V3.6 - STRUCTURED SAFETY EVENT EXTRACTOR
# ============================================================
# Purpose:
# Convert detected safety events into a structured format:
#
# REPORT
#   ↓
# Activity
# Hazard
# Barrier Failure
# Consequence
# Evidence
# Context
#
# Includes domain-based activity correction for obvious cases
# such as mechanical lifting, work at height, confined space,
# hot work and maintenance.
# ============================================================


# ------------------------------------------------------------
# DOMAIN ACTIVITY OVERRIDE
# ------------------------------------------------------------

def apply_domain_activity_override(report_text, activity):
    """
    Correct obvious activity classifications using strong
    domain evidence before presenting the result to the user.

    This is a prototype domain-rule layer. It does not replace
    the semantic model; it corrects cases where strong keywords
    clearly indicate the activity.
    """

    text = (report_text or "").lower()

    # --------------------------------------------------------
    # Safe Mechanical Lifting
    # --------------------------------------------------------
    if (
        any(term in text for term in [
            "crane",
            "hoist",
            "hoisting",
            "suspended load",
            "suspended pipe",
            "lifting",
            "lifting operation",
            "lifting operations",
            "rigging"
        ])
        and
        any(term in text for term in [
            "pipe",
            "load",
            "lift",
            "worker",
            "dropped",
            "shifted",
            "suspended"
        ])
    ):
        return "Safe Mechanical Lifting"

    # --------------------------------------------------------
    # Work at Height
    # --------------------------------------------------------
    if any(term in text for term in [
        "working at height",
        "work at height",
        "elevated platform",
        "unprotected edge",
        "fall protection",
        "fall arrest",
        "scaffold",
        "scaffolding",
        "roof",
        "height above ground",
        "feet above"
    ]):
        return "Work at Height"

    # --------------------------------------------------------
    # Confined Space
    # --------------------------------------------------------
    if (
        "confined space" in text
        or "storage tank" in text
        or "manhole" in text
        or "inside the tank" in text
        or "inside a tank" in text
        or "inside vessel" in text
    ):
        return "Confined Space Entry"

    # --------------------------------------------------------
    # Hot Work
    # --------------------------------------------------------
    if any(term in text for term in [
        "welding",
        "hot work",
        "cutting",
        "grinding",
        "flame cutting",
        "gas cutting"
    ]):
        return "Hot Work"

    # --------------------------------------------------------
    # Driving / Vehicle Operation
    # --------------------------------------------------------
    if any(term in text for term in [
        "forklift",
        "vehicle",
        "driving",
        "reversing vehicle",
        "reverse vehicle",
        "truck",
        "car",
        "mobile equipment"
    ]):
        return "Driving / Vehicle Operation"

    # --------------------------------------------------------
    # Electrical Work
    # --------------------------------------------------------
    if any(term in text for term in [
        "electrician",
        "energized electrical",
        "energized line",
        "electrical line",
        "electrical panel",
        "electrical work",
        "11 kv",
        "33 kv",
        "high voltage",
        "live electrical"
    ]):
        return "Electrical Work"

    # --------------------------------------------------------
    # Maintenance
    # --------------------------------------------------------
    if any(term in text for term in [
        "maintenance",
        "repair",
        "servicing",
        "equipment maintenance"
    ]):
        return "Maintenance"

    # --------------------------------------------------------
    # If no strong domain evidence exists,
    # keep the semantic model result.
    # --------------------------------------------------------
    return activity


# ------------------------------------------------------------
# Get the strongest semantic concept from a category
# ------------------------------------------------------------

def get_top_concept(concepts):
    """
    Safely extract the highest-scoring concept from a semantic
    analysis category.

    Supports:
        - dictionary format
        - tuple/list format
    """

    if not concepts:
        return {
            "concept": "Unknown",
            "score": 0.0
        }

    best_item = None
    best_score = -1.0

    for item in concepts:

        # ----------------------------------------------------
        # Dictionary format
        # ----------------------------------------------------
        if isinstance(item, dict):

            concept = item.get(
                "concept",
                item.get("name", "Unknown")
            )

            score = item.get(
                "score",
                item.get("similarity", 0)
            )

        # ----------------------------------------------------
        # Tuple / list format
        # ----------------------------------------------------
        elif isinstance(item, (tuple, list)) and len(item) >= 2:

            concept = item[0]
            score = item[1]

        else:
            continue

        # ----------------------------------------------------
        # Convert score safely
        # ----------------------------------------------------
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 0.0

        # ----------------------------------------------------
        # Keep strongest concept
        # ----------------------------------------------------
        if score > best_score:

            best_score = score

            best_item = {
                "concept": str(concept),
                "score": score
            }

    # --------------------------------------------------------
    # Nothing valid found
    # --------------------------------------------------------
    if best_item is None:
        return {
            "concept": "Unknown",
            "score": 0.0
        }

    return best_item


# ------------------------------------------------------------
# Find a category safely
# ------------------------------------------------------------

def get_category(analysis, possible_names):
    """
    Find a category from the semantic analysis using multiple
    possible key names.
    """

    if not isinstance(analysis, dict):
        return []

    for name in possible_names:

        if name in analysis:

            value = analysis[name]

            if value is None:
                return []

            return value

    return []


# ------------------------------------------------------------
# Extract one structured event
# ------------------------------------------------------------

def structure_event(event, report_text=""):
    """
    Convert one analyzed event into a structured safety event.

    Parameters
    ----------
    event : dict
        Event generated by event_analyzer.

    report_text : str
        Complete original report text. Used for strong domain
        activity correction.
    """

    if not isinstance(event, dict):
        event = {}

    analysis = event.get(
        "analysis",
        {}
    )

    if not isinstance(analysis, dict):
        analysis = {}

    # ========================================================
    # ACTIVITY
    # ========================================================

    activities = get_category(
        analysis,
        [
            "activities",
            "activity"
        ]
    )

    activity = get_top_concept(
        activities
    )

    # --------------------------------------------------------
    # Apply domain activity correction
    # --------------------------------------------------------

    original_activity = activity["concept"]

    corrected_activity = apply_domain_activity_override(
        report_text,
        original_activity
    )

    activity["concept"] = corrected_activity

    # ========================================================
    # HAZARD
    # ========================================================

    hazards = get_category(
        analysis,
        [
            "hazards",
            "hazard"
        ]
    )

    hazard = get_top_concept(
        hazards
    )

    # ========================================================
    # BARRIER FAILURE
    # ========================================================

    barriers = get_category(
        analysis,
        [
            "barrier_failures",
            "barrier failure",
            "barriers",
            "barrier"
        ]
    )

    barrier = get_top_concept(
        barriers
    )

    # ========================================================
    # CONSEQUENCE
    # ========================================================

    consequences = get_category(
        analysis,
        [
            "consequences",
            "consequence"
        ]
    )

    consequence = get_top_concept(
        consequences
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence = event.get(
        "sentences",
        []
    )

    if evidence is None:
        evidence = []

    # Make sure evidence is a list
    if isinstance(evidence, str):
        evidence = [evidence]

    # ========================================================
    # RELEVANCE
    # ========================================================

    try:
        relevance = float(
            event.get(
                "relevance",
                0
            )
        )
    except (ValueError, TypeError):
        relevance = 0.0

    # ========================================================
    # CONTEXT
    # ========================================================

    context = event.get(
        "context",
        ""
    )

    if context is None:
        context = ""

    # ========================================================
    # CREATE STRUCTURED EVENT
    # ========================================================

    structured_event = {

        # ----------------------------------------------------
        # Event identity
        # ----------------------------------------------------
        "event_id": event.get(
            "event_id",
            "UNKNOWN"
        ),

        # ----------------------------------------------------
        # Activity
        # ----------------------------------------------------
        "activity": activity["concept"],

        "activity_score": activity["score"],

        # ----------------------------------------------------
        # Keep original semantic activity for debugging
        # ----------------------------------------------------
        "semantic_activity": original_activity,

        # ----------------------------------------------------
        # Hazard
        # ----------------------------------------------------
        "hazard": hazard["concept"],

        "hazard_score": hazard["score"],

        # ----------------------------------------------------
        # Barrier failure
        # ----------------------------------------------------
        "barrier_failure": barrier["concept"],

        "barrier_score": barrier["score"],

        # ----------------------------------------------------
        # Consequence
        # ----------------------------------------------------
        "consequence": consequence["concept"],

        "consequence_score": consequence["score"],

        # ----------------------------------------------------
        # Event relevance
        # ----------------------------------------------------
        "relevance": relevance,

        # ----------------------------------------------------
        # Evidence sentences
        # ----------------------------------------------------
        "evidence": evidence,

        # ----------------------------------------------------
        # Context
        # ----------------------------------------------------
        "context": context
    }

    return structured_event


# ------------------------------------------------------------
# Analyze complete report
# ------------------------------------------------------------

def extract_structured_events(report_text):
    """
    Analyze the complete safety report and convert all detected
    events into structured events.
    """

    if not report_text or not report_text.strip():
        return []

    # --------------------------------------------------------
    # Detect events using the existing event analyzer
    # --------------------------------------------------------

    events = analyze_events(
        report_text
    )

    # --------------------------------------------------------
    # Convert each event to structured format
    # --------------------------------------------------------

    structured_events = []

    for event in events:

        structured_event = structure_event(
            event,
            report_text
        )

        structured_events.append(
            structured_event
        )

    return structured_events


# ------------------------------------------------------------
# Display structured events
# ------------------------------------------------------------

def print_structured_events(events):
    """
    Print structured safety events in a readable terminal format.
    """

    print("\n")
    print("=" * 80)
    print("V3.6 - STRUCTURED SAFETY EVENTS")
    print("=" * 80)

    # --------------------------------------------------------
    # No events
    # --------------------------------------------------------

    if not events:

        print("\nNo safety events detected.")

        return

    # --------------------------------------------------------
    # Print every event
    # --------------------------------------------------------

    for event in events:

        print("\n")

        # ----------------------------------------------------
        # Event ID
        # ----------------------------------------------------

        print(
            f"EVENT ID       : "
            f"E{event['event_id']}"
        )

        # ----------------------------------------------------
        # Activity
        # ----------------------------------------------------

        print(
            f"ACTIVITY       : "
            f"{event['activity']} "
            f"({event['activity_score']:.3f})"
        )

        # Show semantic activity only if it differs
        if (
            event.get("semantic_activity")
            and
            event["semantic_activity"]
            != event["activity"]
        ):

            print(
                f"SEMANTIC MODEL : "
                f"{event['semantic_activity']}"
            )

            print(
                f"DOMAIN OVERRIDE: "
                f"{event['activity']}"
            )

        # ----------------------------------------------------
        # Hazard
        # ----------------------------------------------------

        print(
            f"HAZARD         : "
            f"{event['hazard']} "
            f"({event['hazard_score']:.3f})"
        )

        # ----------------------------------------------------
        # Barrier failure
        # ----------------------------------------------------

        print(
            f"BARRIER FAILURE: "
            f"{event['barrier_failure']} "
            f"({event['barrier_score']:.3f})"
        )

        # ----------------------------------------------------
        # Consequence
        # ----------------------------------------------------

        print(
            f"CONSEQUENCE    : "
            f"{event['consequence']} "
            f"({event['consequence_score']:.3f})"
        )

        # ----------------------------------------------------
        # Relevance
        # ----------------------------------------------------

        print(
            f"RELEVANCE      : "
            f"{event['relevance']:.3f}"
        )

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        print("\nEVIDENCE:")

        if event["evidence"]:

            for sentence in event["evidence"]:

                print(
                    f"  • {sentence}"
                )

        else:

            print(
                "  • No evidence sentence available."
            )

        # ----------------------------------------------------
        # Context
        # ----------------------------------------------------

        print("\nCONTEXT:")

        if event["context"]:

            print(
                f"  {event['context']}"
            )

        else:

            print(
                "  No additional context available."
            )

        print(
            "-" * 80
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Test report - Energy Isolation
    # --------------------------------------------------------

    report = """
    During maintenance of a compressor, the equipment was shut down.
    The isolation valve was closed but the isolation was not verified.
    Residual pressure remained inside the process line.
    Two workers started removing the flange while standing close to the line.
    The supervisor noticed the unsafe condition and immediately stopped the work.
    The permit was reviewed and the isolation was verified before work resumed.
    """

    # --------------------------------------------------------
    # Extract structured events
    # --------------------------------------------------------

    structured_events = extract_structured_events(
        report
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print_structured_events(
        structured_events
    )
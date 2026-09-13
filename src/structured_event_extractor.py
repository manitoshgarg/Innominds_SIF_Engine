from event_analyzer import analyze_events


# ============================================================
# V3.5 - STRUCTURED SAFETY EVENT EXTRACTOR
# ============================================================


# ------------------------------------------------------------
# Get the strongest semantic concept from a category
# ------------------------------------------------------------

def get_top_concept(concepts):

    if not concepts:
        return {
            "concept": "Unknown",
            "score": 0.0
        }

    best_item = None
    best_score = -1.0

    for item in concepts:

        # Dictionary format
        if isinstance(item, dict):

            concept = item.get(
                "concept",
                item.get("name", "Unknown")
            )

            score = item.get(
                "score",
                item.get("similarity", 0)
            )

        # Tuple/list format
        elif isinstance(item, (tuple, list)) and len(item) >= 2:

            concept = item[0]
            score = item[1]

        else:
            continue

        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 0.0

        if score > best_score:

            best_score = score

            best_item = {
                "concept": str(concept),
                "score": score
            }

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

    for name in possible_names:

        if name in analysis:
            return analysis[name]

    return []


# ------------------------------------------------------------
# Extract one structured event
# ------------------------------------------------------------

def structure_event(event):

    analysis = event.get("analysis", {})

    # --------------------------------------------
    # Activity
    # --------------------------------------------

    activities = get_category(
        analysis,
        ["activities", "activity"]
    )

    activity = get_top_concept(activities)

    # --------------------------------------------
    # Hazard
    # --------------------------------------------

    hazards = get_category(
        analysis,
        ["hazards", "hazard"]
    )

    hazard = get_top_concept(hazards)

    # --------------------------------------------
    # Barrier Failure
    # --------------------------------------------

    barriers = get_category(
        analysis,
        [
            "barrier_failures",
            "barrier failure",
            "barriers"
        ]
    )

    barrier = get_top_concept(barriers)

    # --------------------------------------------
    # Consequence
    # --------------------------------------------

    consequences = get_category(
        analysis,
        ["consequences", "consequence"]
    )

    consequence = get_top_concept(consequences)

    # --------------------------------------------
    # Create structured event
    # --------------------------------------------

    structured_event = {

        "event_id": event.get(
            "event_id",
            "UNKNOWN"
        ),

        "activity": activity["concept"],

        "activity_score": activity["score"],

        "hazard": hazard["concept"],

        "hazard_score": hazard["score"],

        "barrier_failure": barrier["concept"],

        "barrier_score": barrier["score"],

        "consequence": consequence["concept"],

        "consequence_score": consequence["score"],

        "relevance": float(
            event.get("relevance", 0)
        ),

        "evidence": event.get(
            "sentences",
            []
        ),

        "context": event.get(
            "context",
            ""
        )
    }

    return structured_event


# ------------------------------------------------------------
# Analyze complete report
# ------------------------------------------------------------

def extract_structured_events(report_text):

    events = analyze_events(report_text)

    structured_events = []

    for event in events:

        structured_event = structure_event(event)

        structured_events.append(
            structured_event
        )

    return structured_events


# ------------------------------------------------------------
# Display structured events
# ------------------------------------------------------------

def print_structured_events(events):

    print("\n")
    print("=" * 80)
    print("V3.5 - STRUCTURED SAFETY EVENTS")
    print("=" * 80)

    if not events:

        print("\nNo safety events detected.")

        return

    for event in events:

        print("\n")
        print(f"EVENT ID       : E{event['event_id']}")

        print(
            f"ACTIVITY       : "
            f"{event['activity']} "
            f"({event['activity_score']:.3f})"
        )

        print(
            f"HAZARD         : "
            f"{event['hazard']} "
            f"({event['hazard_score']:.3f})"
        )

        print(
            f"BARRIER FAILURE: "
            f"{event['barrier_failure']} "
            f"({event['barrier_score']:.3f})"
        )

        print(
            f"CONSEQUENCE    : "
            f"{event['consequence']} "
            f"({event['consequence_score']:.3f})"
        )

        print(
            f"RELEVANCE      : "
            f"{event['relevance']:.3f}"
        )

        print("\nEVIDENCE:")

        for sentence in event["evidence"]:

            print(f"  • {sentence}")

        print("\nCONTEXT:")

        print(
            f"  {event['context']}"
        )

        print("-" * 80)


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

    structured_events = extract_structured_events(
        report
    )

    print_structured_events(
        structured_events
    )
from sentence_analyzer import (
    split_into_sentences,
    analyze_sentence,
    calculate_safety_relevance
)

from semantic_extractor import analyze_report


# --------------------------------------------------
# STEP 1: Find relevant sentences
# --------------------------------------------------

def identify_relevant_sentences(sentences, threshold=0.45):

    results = []

    for i, sentence in enumerate(sentences):

        # First analyze the sentence
        sentence_result = analyze_sentence(sentence)

        # Then calculate its safety relevance
        relevance = calculate_safety_relevance(sentence_result)

        results.append({
            "index": i,
            "sentence": sentence,
            "relevance": relevance
        })

    return results


# --------------------------------------------------
# STEP 2: Add neighboring sentences
# --------------------------------------------------

def expand_context(sentence_results, window=1):

    selected_indices = set()

    for item in sentence_results:

        if item["relevance"] >= 0.45:

            index = item["index"]

            start = max(0, index - window)
            end = min(len(sentence_results), index + window + 1)

            for i in range(start, end):
                selected_indices.add(i)

    return sorted(selected_indices)


# --------------------------------------------------
# STEP 3: Group related sentences
# --------------------------------------------------

def create_event_groups(sentence_results, selected_indices):

    if not selected_indices:
        return []

    groups = []
    current_group = [selected_indices[0]]

    for i in range(1, len(selected_indices)):

        previous = selected_indices[i - 1]
        current = selected_indices[i]

        # Consecutive sentences belong to same event context
        if current == previous + 1:
            current_group.append(current)

        else:
            groups.append(current_group)
            current_group = [current]

    groups.append(current_group)

    return groups


# --------------------------------------------------
# STEP 4: Analyze each event
# --------------------------------------------------

def analyze_events(report_text):

    sentences = split_into_sentences(report_text)

    sentence_results = identify_relevant_sentences(sentences)

    selected_indices = expand_context(sentence_results)

    event_groups = create_event_groups(
        sentence_results,
        selected_indices
    )

    events = []

    for event_number, group in enumerate(event_groups, start=1):

        event_sentences = [
            sentences[i]
            for i in group
        ]

        context = " ".join(event_sentences)

        semantic_analysis = analyze_report(context)

        average_relevance = sum(
            sentence_results[i]["relevance"]
            for i in group
        ) / len(group)

        events.append({
            "event_id": event_number,
            "sentences": event_sentences,
            "context": context,
            "relevance": average_relevance,
            "analysis": semantic_analysis
        })

    return events


# --------------------------------------------------
# STEP 5: Display results
# --------------------------------------------------

def print_event_analysis(events):

    print("\n" + "=" * 80)
    print("SAFETY EVENT CONTEXT ANALYSIS")
    print("=" * 80)

    if not events:
        print("\nNo safety events detected.")
        return

    for event in events:

        print(f"\nEVENT {event['event_id']}")
        print("-" * 80)

        print(
            f"Context relevance: "
            f"{float(event['relevance']):.3f}"
        )

        print("\nEvent Context:")

        for sentence in event["sentences"]:
            print(f"  • {sentence}")

        print("\nSemantic Safety Analysis:")

        analysis = event["analysis"]

        for category, concepts in analysis.items():

            print(f"\n{category.upper()}:")

            if not concepts:
                print("  No concepts found.")
                continue

            for item in concepts:

                # Handle dictionary result
                if isinstance(item, dict):

                    concept = item.get(
                        "concept",
                        item.get("name", "Unknown")
                    )

                    similarity = item.get(
                        "score",
                        item.get("similarity", 0)
                    )

                # Handle tuple/list result
                elif isinstance(item, (tuple, list)) and len(item) >= 2:

                    concept = item[0]
                    similarity = item[1]

                else:

                    concept = str(item)
                    similarity = 0

                try:
                    similarity = float(similarity)
                except (ValueError, TypeError):
                    similarity = 0.0

                print(
                    f"  {str(concept):<35} "
                    f"{similarity:.3f}"
                )

# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    report = """
    During maintenance of a compressor, the equipment was shut down.
    The isolation valve was closed but the isolation was not verified.
    Residual pressure remained inside the process line.
    Two workers started removing the flange while standing close to the line.
    The supervisor noticed the unsafe condition and immediately stopped the work.
    The permit was reviewed and the isolation was verified before work resumed.
    """

    events = analyze_events(report)

    print_event_analysis(events)
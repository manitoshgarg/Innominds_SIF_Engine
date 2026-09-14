import re

from sentence_transformers import SentenceTransformer, util

from safety_knowledge_base import SAFETY_KNOWLEDGE_BASE


# ============================================================
# V3.6 - SENTENCE-LEVEL SAFETY ANALYZER
# ============================================================
#
# Purpose:
#   1. Split safety reports into reliable sentences
#   2. Handle abbreviations such as "approx."
#   3. Protect decimal numbers such as "20.5 ft"
#   4. Convert sentences into embeddings
#   5. Compare sentences with the safety knowledge base
#   6. Calculate safety relevance
#
# This module provides the semantic analysis layer used by
# the event extraction pipeline.
# ============================================================


# ------------------------------------------------------------
# 1. LOAD MODEL
# ------------------------------------------------------------

print("Loading semantic model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Semantic model loaded.")


# ------------------------------------------------------------
# 2. PREPARE KNOWLEDGE BASE EMBEDDINGS
# ------------------------------------------------------------

knowledge_embeddings = {}

for category, concepts in SAFETY_KNOWLEDGE_BASE.items():

    names = list(
        concepts.keys()
    )

    descriptions = [
        concepts[name]
        for name in names
    ]

    embeddings = model.encode(
        descriptions,
        convert_to_tensor=True
    )

    knowledge_embeddings[category] = {
        "names": names,
        "embeddings": embeddings
    }


# ------------------------------------------------------------
# 3. SENTENCE SEGMENTATION
# ------------------------------------------------------------

def split_into_sentences(report_text):
    """
    Split a safety report into sentences while protecting
    common abbreviations and decimal numbers.

    Examples that should remain together:

        approx. 450 kg
        20.5 feet
        e.g. crane operation
        i.e. isolation verification

    Returns
    -------
    list[str]
        Clean sentence list.
    """

    if not report_text:
        return []

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        report_text
    ).strip()

    if not text:
        return []

    # --------------------------------------------------------
    # Protect common abbreviations
    # --------------------------------------------------------

    protected_abbreviations = {
        "approx.": "__APPROX__",
        "e.g.": "__EG__",
        "i.e.": "__IE__",
        "etc.": "__ETC__",
        "mr.": "__MR__",
        "mrs.": "__MRS__",
        "dr.": "__DR__",
        "no.": "__NO__"
    }

    for original, replacement in protected_abbreviations.items():

        text = re.sub(
            re.escape(original),
            replacement,
            text,
            flags=re.IGNORECASE
        )

    # --------------------------------------------------------
    # Protect decimal numbers
    #
    # Example:
    #     20.5 ft
    #     11.7 kV
    #     3.14 metres
    # --------------------------------------------------------

    text = re.sub(
        r"(?<=\d)\.(?=\d)",
        "__DECIMAL__",
        text
    )

    # --------------------------------------------------------
    # Protect common units / measurement expressions
    #
    # This helps prevent unwanted segmentation in technical
    # safety reports.
    # --------------------------------------------------------

    text = re.sub(
        r"(\d+)\s*\.\s*(kg|kv|bar|psi|mm|cm|m|ft|feet|%)",
        r"\1__UNIT_DOT__\2",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Sentence segmentation
    #
    # Split only when punctuation is followed by whitespace
    # and a likely sentence-start character.
    # --------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text
    )

    # --------------------------------------------------------
    # Restore protected content
    # --------------------------------------------------------

    restored_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # Restore abbreviations
        sentence = sentence.replace(
            "__APPROX__",
            "approx."
        )

        sentence = sentence.replace(
            "__EG__",
            "e.g."
        )

        sentence = sentence.replace(
            "__IE__",
            "i.e."
        )

        sentence = sentence.replace(
            "__ETC__",
            "etc."
        )

        sentence = sentence.replace(
            "__MR__",
            "Mr."
        )

        sentence = sentence.replace(
            "__MRS__",
            "Mrs."
        )

        sentence = sentence.replace(
            "__DR__",
            "Dr."
        )

        sentence = sentence.replace(
            "__NO__",
            "No."
        )

        # Restore decimal points
        sentence = sentence.replace(
            "__DECIMAL__",
            "."
        )

        # Restore protected unit pattern
        sentence = sentence.replace(
            "__UNIT_DOT__",
            "."
        )

        restored_sentences.append(
            sentence
        )

    return restored_sentences


# ------------------------------------------------------------
# 4. ANALYZE ONE SENTENCE
# ------------------------------------------------------------

def analyze_sentence(sentence, top_k=2):
    """
    Perform semantic similarity analysis for one sentence.

    Parameters
    ----------
    sentence : str
        Safety report sentence.

    top_k : int
        Number of top concepts returned per category.

    Returns
    -------
    dict
        Semantic analysis grouped by safety category.
    """

    if not sentence or not sentence.strip():
        return {}

    # --------------------------------------------------------
    # Generate sentence embedding
    # --------------------------------------------------------

    sentence_embedding = model.encode(
        sentence,
        convert_to_tensor=True
    )

    sentence_result = {}

    # --------------------------------------------------------
    # Compare against every knowledge-base category
    # --------------------------------------------------------

    for category, data in knowledge_embeddings.items():

        similarities = util.cos_sim(
            sentence_embedding,
            data["embeddings"]
        )[0]

        number_of_results = min(
            top_k,
            len(data["names"])
        )

        if number_of_results == 0:
            sentence_result[category] = []
            continue

        top_indices = similarities.argsort(
            descending=True
        )[:number_of_results]

        results = []

        for index in top_indices:

            index = int(index)

            results.append({
                "name": data["names"][index],
                "score": round(
                    float(similarities[index]),
                    3
                )
            })

        sentence_result[category] = results

    return sentence_result


# ------------------------------------------------------------
# 5. CALCULATE SAFETY RELEVANCE
# ------------------------------------------------------------

def calculate_safety_relevance(sentence_result):
    """
    Calculate the highest semantic safety relevance score
    across all detected safety concepts.
    """

    if not sentence_result:
        return 0.0

    scores = []

    for category, concepts in sentence_result.items():

        if not concepts:
            continue

        for concept in concepts:

            try:
                score = float(
                    concept.get(
                        "score",
                        0.0
                    )
                )
            except (ValueError, TypeError, AttributeError):

                score = 0.0

            scores.append(
                score
            )

    if not scores:
        return 0.0

    # Highest semantic safety score
    return max(scores)


# ------------------------------------------------------------
# 6. ANALYZE COMPLETE REPORT
# ------------------------------------------------------------

def analyze_report(report_text):
    """
    Analyze every sentence in a complete safety report.

    Returns sentences ordered by safety relevance.
    """

    if not report_text or not report_text.strip():
        return []

    # --------------------------------------------------------
    # Split report
    # --------------------------------------------------------

    sentences = split_into_sentences(
        report_text
    )

    analyzed_sentences = []

    # --------------------------------------------------------
    # Analyze every sentence
    # --------------------------------------------------------

    for sentence in sentences:

        analysis = analyze_sentence(
            sentence
        )

        relevance = calculate_safety_relevance(
            analysis
        )

        analyzed_sentences.append({
            "sentence": sentence,
            "safety_relevance": relevance,
            "analysis": analysis
        })

    # --------------------------------------------------------
    # Highest relevance first
    # --------------------------------------------------------

    analyzed_sentences.sort(
        key=lambda x: x["safety_relevance"],
        reverse=True
    )

    return analyzed_sentences


# ------------------------------------------------------------
# 7. PRINT RESULTS
# ------------------------------------------------------------

def print_report_analysis(results):
    """
    Display sentence-level semantic analysis in the terminal.
    """

    print("\n")
    print("=" * 70)
    print("SENTENCE-LEVEL SAFETY ANALYSIS")
    print("=" * 70)

    if not results:

        print("\nNo sentences detected.")

        return

    for i, item in enumerate(
        results,
        start=1
    ):

        print("\n")
        print(
            f"SENTENCE {i}"
        )

        print(
            "-" * 70
        )

        print(
            item["sentence"]
        )

        print(
            f"\nSafety relevance: "
            f"{item['safety_relevance']:.3f}"
        )

        # ----------------------------------------------------
        # Show top concept from each category
        # ----------------------------------------------------

        for category, concepts in item[
            "analysis"
        ].items():

            if concepts:

                top = concepts[0]

                print(
                    f"  {category}: "
                    f"{top['name']} "
                    f"({top['score']:.3f})"
                )


# ============================================================
# 8. TEST
# ============================================================

if __name__ == "__main__":

    report = """
    During the morning maintenance activity, the crew
    prepared the compressor for inspection.

    The equipment was believed to have been isolated
    before the work started.

    During verification, pressure was found to still
    be present in the connected section of the pipeline.

    The isolation had not been independently verified
    before personnel approached the equipment.

    Two workers were positioned near the equipment
    while the verification was being performed.

    The supervisor stopped the activity and instructed
    the team to re-establish and verify the isolation
    before continuing the maintenance work.

    The required permit documentation was subsequently
    reviewed by the supervisor.

    A suspended pipe with a weight approx. 450 kg
    was moved using a hoist.
    """

    # --------------------------------------------------------
    # Test sentence segmentation first
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("SENTENCE SEGMENTATION TEST")
    print("=" * 70)

    test_sentences = split_into_sentences(
        report
    )

    for i, sentence in enumerate(
        test_sentences,
        start=1
    ):

        print(
            f"{i}. {sentence}"
        )

    # --------------------------------------------------------
    # Full semantic analysis
    # --------------------------------------------------------

    results = analyze_report(
        report
    )

    print_report_analysis(
        results
    )
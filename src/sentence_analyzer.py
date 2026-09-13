import re

from sentence_transformers import SentenceTransformer, util

from safety_knowledge_base import SAFETY_KNOWLEDGE_BASE


# --------------------------------------------------
# 1. LOAD MODEL
# --------------------------------------------------

print("Loading semantic model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


# --------------------------------------------------
# 2. PREPARE KNOWLEDGE BASE EMBEDDINGS
# --------------------------------------------------

knowledge_embeddings = {}

for category, concepts in SAFETY_KNOWLEDGE_BASE.items():

    names = list(concepts.keys())

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


# --------------------------------------------------
# 3. SPLIT REPORT INTO SENTENCES
# --------------------------------------------------

def split_into_sentences(report_text):

    # Remove unnecessary whitespace
    text = re.sub(r"\s+", " ", report_text).strip()

    # Basic sentence segmentation
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    # Remove empty sentences
    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    return sentences


# --------------------------------------------------
# 4. ANALYZE ONE SENTENCE
# --------------------------------------------------

def analyze_sentence(sentence, top_k=2):

    sentence_embedding = model.encode(
        sentence,
        convert_to_tensor=True
    )

    sentence_result = {}

    for category, data in knowledge_embeddings.items():

        similarities = util.cos_sim(
            sentence_embedding,
            data["embeddings"]
        )[0]

        number_of_results = min(
            top_k,
            len(data["names"])
        )

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


# --------------------------------------------------
# 5. CALCULATE SAFETY RELEVANCE
# --------------------------------------------------

def calculate_safety_relevance(sentence_result):

    scores = []

    for category, concepts in sentence_result.items():

        for concept in concepts:

            scores.append(
                concept["score"]
            )

    if not scores:
        return 0.0

    # Highest semantic safety score
    return max(scores)


# --------------------------------------------------
# 6. ANALYZE COMPLETE REPORT
# --------------------------------------------------

def analyze_report(report_text):

    sentences = split_into_sentences(
        report_text
    )

    analyzed_sentences = []

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

    # Highest relevance first
    analyzed_sentences.sort(
        key=lambda x: x["safety_relevance"],
        reverse=True
    )

    return analyzed_sentences


# --------------------------------------------------
# 7. PRINT RESULTS
# --------------------------------------------------

def print_report_analysis(results):

    print("\n")
    print("=" * 70)
    print("SENTENCE-LEVEL SAFETY ANALYSIS")
    print("=" * 70)

    for i, item in enumerate(results, start=1):

        print("\n")
        print(f"SENTENCE {i}")
        print("-" * 70)

        print(item["sentence"])

        print(
            f"\nSafety relevance: "
            f"{item['safety_relevance']}"
        )

        # Show top concept from each category
        for category, concepts in item["analysis"].items():

            if concepts:

                top = concepts[0]

                print(
                    f"  {category}: "
                    f"{top['name']} "
                    f"({top['score']})"
                )


# --------------------------------------------------
# 8. TEST
# --------------------------------------------------

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
    """

    results = analyze_report(report)

    print_report_analysis(results)
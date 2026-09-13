from sentence_transformers import SentenceTransformer, util
from safety_knowledge_base import SAFETY_KNOWLEDGE_BASE


# --------------------------------------------------
# 1. LOAD MODEL
# --------------------------------------------------

print("Loading semantic model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


# --------------------------------------------------
# 2. PREPARE KNOWLEDGE BASE
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
# 3. FIND RELEVANT CONCEPTS
# --------------------------------------------------

def find_concepts(report_text, category, top_k=3):

    report_embedding = model.encode(
        report_text,
        convert_to_tensor=True
    )

    category_data = knowledge_embeddings[category]

    similarities = util.cos_sim(
        report_embedding,
        category_data["embeddings"]
    )[0]

    # Don't return more results than available
    number_of_results = min(
        top_k,
        len(category_data["names"])
    )

    top_indices = similarities.argsort(
        descending=True
    )[:number_of_results]

    results = []

    for index in top_indices:

        index = int(index)

        results.append({
            "name": category_data["names"][index],
            "score": round(
                float(similarities[index]),
                3
            )
        })

    return results


# --------------------------------------------------
# 4. ANALYZE COMPLETE REPORT
# --------------------------------------------------

def analyze_report(report_text):

    result = {}

    for category in SAFETY_KNOWLEDGE_BASE:

        result[category] = find_concepts(
            report_text,
            category,
            top_k=3
        )

    return result


# --------------------------------------------------
# 5. PRINT RESULTS
# --------------------------------------------------

def print_analysis(result):

    print("\n")
    print("=" * 65)
    print("SEMANTIC SAFETY ANALYSIS")
    print("=" * 65)

    for category, concepts in result.items():

        print(f"\n{category.upper()}")

        print("-" * 45)

        for concept in concepts:

            print(
                f"{concept['name']:<35}"
                f" Score: {concept['score']}"
            )


# --------------------------------------------------
# 6. TEST
# --------------------------------------------------

if __name__ == "__main__":

    report = """
    During maintenance activities on the compressor unit,
    the maintenance crew started intervention after the equipment
    was believed to have been isolated. During verification,
    pressure was found to still be present in the connected
    section of the pipeline. The isolation had not been
    independently verified before personnel approached the
    equipment. The supervisor stopped the work and instructed
    the team to re-establish and verify the isolation before
    continuing the maintenance activity.
    """

    analysis = analyze_report(report)

    print_analysis(analysis)
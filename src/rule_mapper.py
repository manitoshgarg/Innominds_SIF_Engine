"""
INNOMINDS SIH 2026
Life-Saving Rule Semantic Mapper

Purpose:
Map a free-text safety report to the most relevant
Life-Saving Rule using semantic embeddings.

This is a prototype/demo component.
"""

from sentence_transformers import SentenceTransformer, util


# ---------------------------------------------------------
# 1. Life-Saving Rule knowledge base
# ---------------------------------------------------------

LIFE_SAVING_RULES = {
    "Confined Space": (
        "Entry into a confined space requires authorization, "
        "atmospheric testing, safe entry controls, an attendant "
        "where required, and emergency preparedness."
    ),

    "Energy Isolation": (
        "Hazardous energy must be isolated, locked out, "
        "depressurized or otherwise controlled, and verified "
        "before maintenance or intervention."
    ),

    "Hot Work": (
        "Hot work such as welding, cutting or grinding requires "
        "appropriate authorization, gas testing and controls "
        "to prevent fire or explosion."
    ),

    "Line of Fire": (
        "Personnel must stay out of areas where released energy, "
        "moving equipment, pressure, vehicles or objects can "
        "cause serious injury."
    ),

    "Working at Height": (
        "Work at height requires appropriate fall prevention "
        "and fall protection controls."
    ),

    "Lifting Operations": (
        "Personnel must remain clear of suspended loads and "
        "lifting operations must be properly controlled."
    ),

    "Driving": (
        "Vehicle operations require controls for safe driving, "
        "pedestrian separation, reversing and traffic movement."
    ),
}


# ---------------------------------------------------------
# 2. Load pretrained embedding model
# ---------------------------------------------------------

print("Loading Sentence Transformer model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Model loaded successfully.")


# ---------------------------------------------------------
# 3. Create embeddings for Life-Saving Rules
# ---------------------------------------------------------

rule_names = list(LIFE_SAVING_RULES.keys())

rule_descriptions = list(LIFE_SAVING_RULES.values())

rule_embeddings = model.encode(
    rule_descriptions,
    convert_to_tensor=True
)


# ---------------------------------------------------------
# 4. Function to map report → Life-Saving Rule
# ---------------------------------------------------------

def map_life_saving_rule(report_text, top_k=3):

    # Convert report into embedding
    report_embedding = model.encode(
        report_text,
        convert_to_tensor=True
    )

    # Calculate semantic similarity
    similarities = util.cos_sim(
        report_embedding,
        rule_embeddings
    )[0]

    # Sort highest similarity first
    ranked_indices = similarities.argsort(
        descending=True
    )

    results = []

    for index in ranked_indices[:top_k]:

        index = int(index)

        results.append({
            "rule": rule_names[index],
            "similarity": float(similarities[index])
        })

    return results


# ---------------------------------------------------------
# 5. Test the mapper
# ---------------------------------------------------------

if __name__ == "__main__":

    test_reports = [

        "Worker entered a vessel without checking oxygen levels.",

        "A technician opened a valve without confirming that "
        "the pipeline was isolated and depressurized.",

        "Welding was started near hydrocarbon vapour without "
        "gas testing.",

        "A worker stood beneath a suspended load during crane lifting.",

        "A contractor worked at height without connecting "
        "the fall protection lanyard."
    ]

    print("\n" + "=" * 60)
    print("INNOMINDS LIFE-SAVING RULE MAPPER")
    print("=" * 60)

    for report in test_reports:

        results = map_life_saving_rule(report)

        print("\nREPORT:")
        print(report)

        print("\nTOP MATCHES:")

        for rank, result in enumerate(results, start=1):

            print(
                f"{rank}. "
                f"{result['rule']} "
                f"→ similarity: "
                f"{result['similarity']:.3f}"
            )

        print("-" * 60)
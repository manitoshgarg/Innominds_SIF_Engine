import re
from sentence_transformers import SentenceTransformer, util


# ============================================================
# IOGP LIFE-SAVING RULES
# ============================================================

LIFE_SAVING_RULES = {
    "Bypassing Safety Controls": (
        "Obtain authorisation before overriding or disabling "
        "safety controls or crossing safety barriers."
    ),

    "Confined Space": (
        "Obtain authorisation before entering a confined space. "
        "Confirm isolation, atmospheric testing, ventilation, "
        "attendant and rescue arrangements."
    ),

    "Driving": (
        "Follow safe driving rules and control vehicle movement, "
        "journey management, reversing and pedestrian interaction."
    ),

    "Energy Isolation": (
        "Verify isolation and zero energy before work begins. "
        "Identify energy sources, isolate and lock out hazardous "
        "energy and verify residual or stored energy."
    ),

    "Hot Work": (
        "Control flammables and ignition sources during welding, "
        "cutting, grinding and other hot work. Perform gas testing "
        "where required."
    ),

    "Line of Fire": (
        "Keep yourself and others out of the line of fire from "
        "moving objects, vehicles, pressure releases, dropped "
        "objects and uncontrolled stored energy."
    ),

    "Safe Mechanical Lifting": (
        "Plan lifting operations and control the area. Inspect "
        "lifting equipment and loads, establish exclusion zones "
        "and never walk under a suspended load."
    ),

    "Work Authorisation": (
        "Work with a valid permit when required and confirm that "
        "hazards are controlled before starting work."
    ),

    "Working at Height": (
        "Protect yourself against falls when working at height. "
        "Use appropriate fall protection and secure tools and "
        "materials against dropped objects."
    ),
}


print("Loading semantic model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded successfully.")


# ============================================================
# DOMAIN KEYWORDS
# ============================================================

RULE_PATTERNS = {

    "Energy Isolation": [
        r"\bisolation\b",
        r"\bisolated\b",
        r"\blockout\b",
        r"\block out\b",
        r"\bloto\b",
        r"\bzero energy\b",
        r"\bresidual pressure\b",
        r"\bstored energy\b",
        r"\btrapped pressure\b",
        r"\bdepressur",
        r"\bde-energ",
        r"\benergy source",
        r"\bisolation.*verified",
        r"\bisolation.*not verified",
    ],

    "Safe Mechanical Lifting": [
        r"\bcrane\b",
        r"\bhoist\b",
        r"\bhoisting\b",
        r"\blifting\b",
        r"\blifted\b",
        r"\bsuspended load\b",
        r"\bsuspended pipe\b",
        r"\brigging\b",
        r"\bsling\b",
        r"\bload\b.{0,40}\bsuspended\b",
        r"\bpipe\b.{0,60}\bhoist\b",
        r"\bpipe\b.{0,60}\bcrane\b",
    ],

    "Working at Height": [
        r"\bworking at height\b",
        r"\belevated platform\b",
        r"\bscaffold\b",
        r"\broof\b",
        r"\btower\b",
        r"\b\d+\s*(ft|feet|foot|metre|meter)\b",
        r"\bunprotected edge\b",
        r"\bfall protection\b",
        r"\bharness\b",
        r"\blanyard\b",
        r"\btie[d]?\s*off\b",
    ],

    "Confined Space": [
        r"\bconfined space\b",
        r"\bstorage tank\b",
        r"\bvessel\b",
        r"\bmanhole\b",
        r"\boxygen\b",
        r"\batmospheric testing\b",
        r"\bgas testing\b",
        r"\bhazardous atmosphere\b",
        r"\btoxic atmosphere\b",
        r"\binadequate ventilation\b",
    ],

    "Hot Work": [
        r"\bhot work\b",
        r"\bweld",
        r"\bwelding\b",
        r"\bcutting\b",
        r"\bgrinding\b",
        r"\bignition source\b",
        r"\bspark",
        r"\bflammable vapou?r\b",
        r"\bhydrocarbon vapou?r\b",
    ],

    "Driving": [
        r"\bforklift\b",
        r"\bvehicle\b",
        r"\btruck\b",
        r"\bdriver\b",
        r"\bdriving\b",
        r"\breversing\b",
        r"\bbacking\b",
        r"\bmobile equipment\b",
        r"\bpedestrian\b",
    ],

    "Line of Fire": [
        r"\bline of fire\b",
        r"\bstruck by\b",
        r"\bcaught between\b",
        r"\bpressure release\b",
        r"\bdropped object\b",
        r"\bmoving object\b",
        r"\bexclusion zone\b",
        r"\bdanger zone\b",
    ],

    "Bypassing Safety Controls": [
        r"\bbypassed\b",
        r"\bbypass\b",
        r"\boverride\b",
        r"\boverridden\b",
        r"\bdisabled safety\b",
        r"\bsafety control.*disabled\b",
        r"\bbarrier.*crossed\b",
    ],

    "Work Authorisation": [
        r"\bpermit\b",
        r"\bwork authorization\b",
        r"\bwork authorisation\b",
        r"\bpermit to work\b",
    ],
}


# ============================================================
# DOMAIN SCORING
# ============================================================

def domain_rule_scores(report_text):

    text = report_text.lower()

    scores = {
        rule: 0
        for rule in LIFE_SAVING_RULES
    }

    matched_terms = {
        rule: []
        for rule in LIFE_SAVING_RULES
    }

    for rule, patterns in RULE_PATTERNS.items():

        for pattern in patterns:

            matches = re.findall(pattern, text)

            if matches:

                scores[rule] += len(matches)
                matched_terms[rule].append(pattern)

    return scores, matched_terms


# ============================================================
# SPECIAL PRIORITY LOGIC
# ============================================================

def determine_primary_rule(report_text):

    text = report_text.lower()

    domain_scores, matched_terms = domain_rule_scores(text)

    # --------------------------------------------------------
    # ENERGY ISOLATION
    # --------------------------------------------------------

    if (
        re.search(r"isolation", text)
        and
        re.search(
            r"(not verified|not properly isolated|"
            r"residual pressure|stored energy|"
            r"trapped pressure|zero energy|"
            r"depressur)",
            text
        )
    ):
        return "Energy Isolation", matched_terms["Energy Isolation"]

    # --------------------------------------------------------
    # SAFE MECHANICAL LIFTING
    # --------------------------------------------------------

    if (
        re.search(
            r"(crane|hoist|hoisting|lifting|rigging|"
            r"suspended load|suspended pipe)",
            text
        )
        and
        re.search(
            r"(load|pipe|worker|person|exclusion|"
            r"below|beneath|fell|dropped|shifted|moved)",
            text
        )
    ):
        return "Safe Mechanical Lifting", matched_terms["Safe Mechanical Lifting"]

    # --------------------------------------------------------
    # WORKING AT HEIGHT
    # --------------------------------------------------------

    if re.search(
        r"(working at height|elevated platform|"
        r"unprotected edge|fall protection|"
        r"\d+\s*(ft|feet|foot|metre|meter)\s+above)",
        text
    ):
        return "Working at Height", matched_terms["Working at Height"]

    # --------------------------------------------------------
    # CONFINED SPACE
    # --------------------------------------------------------

    if (
        re.search(
            r"(confined space|storage tank|vessel|manhole)",
            text
        )
        and
        re.search(
            r"(oxygen|atmosphere|gas|ventilation)",
            text
        )
    ):
        return "Confined Space", matched_terms["Confined Space"]

    # --------------------------------------------------------
    # HOT WORK
    # --------------------------------------------------------

    if (
        re.search(
            r"(welding|weld|cutting|grinding|hot work)",
            text
        )
        and
        re.search(
            r"(flammable|hydrocarbon|vapour|vapor|gas|ignition)",
            text
        )
    ):
        return "Hot Work", matched_terms["Hot Work"]

    # --------------------------------------------------------
    # DRIVING
    # --------------------------------------------------------

    if re.search(
        r"(forklift|vehicle|truck|reversing|"
        r"pedestrian|mobile equipment)",
        text
    ):
        return "Driving", matched_terms["Driving"]

    # --------------------------------------------------------
    # FALLBACK: DOMAIN SCORE
    # --------------------------------------------------------

    best_rule = max(
        domain_scores,
        key=domain_scores.get
    )

    if domain_scores[best_rule] > 0:

        return best_rule, matched_terms[best_rule]

    return None, []


# ============================================================
# MAIN MAPPER
# ============================================================

def map_life_saving_rule(report_text, top_k=3):

    if not report_text or not report_text.strip():
        raise ValueError("Report text cannot be empty.")

    # --------------------------------------------------------
    # Semantic similarity
    # --------------------------------------------------------

    rule_names = list(LIFE_SAVING_RULES.keys())

    rule_descriptions = [
        LIFE_SAVING_RULES[name]
        for name in rule_names
    ]

    report_embedding = model.encode(
        report_text,
        convert_to_tensor=True
    )

    rule_embeddings = model.encode(
        rule_descriptions,
        convert_to_tensor=True
    )

    similarities = util.cos_sim(
        report_embedding,
        rule_embeddings
    )[0]

    semantic_results = []

    for index, score in enumerate(similarities):

        semantic_results.append({
            "rule": rule_names[index],
            "score": float(score)
        })

    semantic_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Domain rule
    # --------------------------------------------------------

    primary_rule, matched_terms = determine_primary_rule(
        report_text
    )

    # --------------------------------------------------------
    # Build result
    # --------------------------------------------------------

    if primary_rule:

        ordered_rules = [primary_rule]

        for item in semantic_results:

            if item["rule"] != primary_rule:
                ordered_rules.append(item["rule"])

            if len(ordered_rules) >= top_k:
                break

        results = []

        for rule in ordered_rules:

            semantic_score = next(
                (
                    item["score"]
                    for item in semantic_results
                    if item["rule"] == rule
                ),
                0.0
            )

            if rule == primary_rule:

                match_type = "Domain evidence + semantic match"
                match_strength = "Strong"

            else:

                match_type = "Semantic match"
                match_strength = "Supporting"

            results.append({
                "rule": rule,
                "score": semantic_score,
                "match_type": match_type,
                "match_strength": match_strength,
            })

    else:

        results = []

        for item in semantic_results[:top_k]:

            results.append({
                "rule": item["rule"],
                "score": item["score"],
                "match_type": "Semantic match",
                "match_strength": "Supporting",
            })

    return results
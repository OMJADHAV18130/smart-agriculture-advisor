"""
Knowledge base for the Smart Agriculture Advisory Expert System.

All agricultural knowledge lives here as plain IF-THEN Rule objects so the
rules are easy to read, edit, and extend without touching the engine or API.

NOTE ON THRESHOLDS: the moisture and temperature cut-offs below are
ILLUSTRATIVE demo thresholds chosen for a classroom project. They are not
validated agronomic standards. In a real system they would come from
agronomy references and local crop research.

All advice is deliberately conservative: symptoms point to *possible*
causes, never confirmed diagnoses, and no pesticide or fertilizer
quantities are ever prescribed.
"""

from typing import Dict, List, Tuple

from .engine import Condition, Fact, Rule

# ---------------------------------------------------------------------------
# Configurable thresholds (ILLUSTRATIVE demo values, not agronomic standards)
# ---------------------------------------------------------------------------
THRESHOLDS: Dict[str, int] = {
    "soil_moisture_low_max": 35,    # <= 35%  -> "low"
    "soil_moisture_high_min": 70,   # >= 70%  -> "high"
    "temperature_high_min": 32,     # >= 32 C -> "high"
}


def normalize_observations(crop: str, soil_moisture: int,
                           temperature: float, rainfall: str,
                           symptom: str) -> List[Fact]:
    """Turn raw user inputs into symbolic facts.

    Numeric observations (moisture %, temperature C) are binned into simple
    symbolic labels ("low"/"mid"/"high") so the rule engine can work with
    exact-match facts. This binning is *input normalization*, not inference;
    all reasoning about those labels is done by the rules below.
    """
    if soil_moisture <= THRESHOLDS["soil_moisture_low_max"]:
        moisture = "low"
    elif soil_moisture >= THRESHOLDS["soil_moisture_high_min"]:
        moisture = "high"
    else:
        moisture = "mid"

    temperature_label = "high" if temperature >= THRESHOLDS["temperature_high_min"] else "normal"

    return [
        ("crop", crop.lower()),
        ("soil_moisture", moisture),
        ("temperature", temperature_label),
        ("rainfall", rainfall.lower()),
        ("symptom", symptom.lower().replace(" ", "_")),
    ]


# ---------------------------------------------------------------------------
# The IF-THEN rules
# ---------------------------------------------------------------------------
C = Condition

RULES: List[Rule] = [
    # --- Irrigation ------------------------------------------------------
    Rule(
        rule_id="R01",
        name="Irrigation likely needed",
        category="irrigation",
        conditions=(C("soil_moisture", "low"), C("rainfall", "no")),
        conclusions=(("irrigation", "needed"), ("water_stress", "possible")),
        explanation="Soil is dry and there has been no recent rain, so the crop may need water.",
    ),
    Rule(
        rule_id="R02",
        name="Check soil before irrigating",
        category="irrigation",
        conditions=(C("soil_moisture", "low"), C("rainfall", "unknown")),
        conclusions=(("irrigation", "check_first"),),
        explanation="Soil is dry but rainfall history is unknown, so check the field before watering.",
    ),
    Rule(
        rule_id="R03",
        name="Irrigation not needed, watch for waterlogging",
        category="irrigation",
        conditions=(C("soil_moisture", "high"), C("rainfall", "yes")),
        conclusions=(("irrigation", "not_needed"), ("waterlogging", "possible")),
        explanation="Soil is already wet and it has rained recently, so extra irrigation is not needed.",
    ),
    Rule(
        rule_id="R04",
        name="Root zone may be too wet",
        category="soil_nutrient",
        conditions=(C("waterlogging", "possible"),),
        conclusions=(("soil_advice", "improve_drainage"),),
        explanation="Prolonged wet soil can reduce oxygen around roots, so drainage is worth checking.",
    ),

    # --- Heat / water stress --------------------------------------------
    Rule(
        rule_id="R05",
        name="Possible heat and water stress",
        category="stress",
        conditions=(C("temperature", "high"), C("soil_moisture", "low")),
        conclusions=(("stress", "heat_and_water"),),
        explanation="High temperature together with dry soil strongly suggests combined heat and water stress.",
    ),
    Rule(
        rule_id="R06",
        name="Heat stress watch",
        category="stress",
        conditions=(C("temperature", "high"),),
        conclusions=(("stress", "heat_watch"),),
        explanation="Temperatures are high, so keep watching for wilting or leaf scorch even if soil looks moist.",
    ),

    # --- Leaf symptoms ---------------------------------------------------
    Rule(
        rule_id="R07",
        name="Yellowing may mean underwatering",
        category="leaf_symptoms",
        conditions=(C("symptom", "yellowing_leaves"), C("soil_moisture", "low")),
        conclusions=(("leaf_diagnosis", "possible_underwatering"),),
        explanation="Yellowing leaves combined with dry soil can indicate the plant is not getting enough water.",
    ),
    Rule(
        rule_id="R08",
        name="Yellowing may mean a nutrient problem",
        category="leaf_symptoms",
        conditions=(C("symptom", "yellowing_leaves"),),
        conclusions=(("leaf_diagnosis", "possible_nutrient_issue"),),
        explanation="Yellowing can also point to a nutrient issue, so a soil test is a sensible next step.",
    ),
    Rule(
        rule_id="R09",
        name="Leaf spots in wet weather",
        category="leaf_symptoms",
        conditions=(C("symptom", "leaf_spots"), C("rainfall", "yes")),
        conclusions=(("leaf_diagnosis", "possible_fungal_issue"),),
        explanation="Spots on leaves during wet weather are often associated with fungal or bacterial leaf problems.",
    ),
    Rule(
        rule_id="R10",
        name="Leaf spots, cause uncertain",
        category="leaf_symptoms",
        conditions=(C("symptom", "leaf_spots"),),
        conclusions=(("leaf_diagnosis", "spots_observed"),),
        explanation="Leaf spots alone are not enough to name a cause, so close monitoring is advised.",
    ),

    # --- Pest monitoring -------------------------------------------------
    Rule(
        rule_id="R11",
        name="Scout for pests",
        category="pest",
        conditions=(C("symptom", "insects_and_leaf_damage"),),
        conclusions=(("pest_action", "scout"),),
        explanation="Chewed or damaged leaves suggest insects; inspect plants to identify the pest before any action.",
    ),
    Rule(
        rule_id="R12",
        name="Wilting with dry soil looks like water stress",
        category="stress",
        conditions=(C("symptom", "wilting"), C("soil_moisture", "low")),
        conclusions=(("stress", "possible_drought_wilting"),),
        explanation="Wilting while the soil is dry usually points to too little water rather than disease.",
    ),
    Rule(
        rule_id="R13",
        name="Wilting with wet soil needs a closer look",
        category="stress",
        conditions=(C("symptom", "wilting"), C("soil_moisture", "high")),
        conclusions=(("stress", "possible_root_issue"),),
        explanation="Wilting in wet soil can signal root damage or poor aeration, so roots and drainage should be checked.",
    ),

    # --- Soil / nutrient checks ------------------------------------------
    Rule(
        rule_id="R14",
        name="Keep monitoring dry soil",
        category="soil_nutrient",
        conditions=(C("soil_moisture", "low"),),
        conclusions=(("soil_advice", "monitor_moisture"),),
        explanation="Soil moisture is below the demo threshold, so monitor it regularly (illustrative threshold).",
    ),
    Rule(
        rule_id="R15",
        name="Rice prefers wetter conditions",
        category="soil_nutrient",
        conditions=(C("crop", "rice"), C("soil_moisture", "low")),
        conclusions=(("soil_advice", "rice_prefers_wet"),),
        explanation="Rice generally tolerates wetter soil than other crops, so dry soil deserves attention.",
    ),
    Rule(
        rule_id="R16",
        name="Yellowing plus dry soil may involve nutrients",
        category="soil_nutrient",
        conditions=(C("leaf_diagnosis", "possible_nutrient_issue"), C("soil_moisture", "low")),
        conclusions=(("soil_advice", "consider_soil_test"),),
        explanation="When yellowing coincides with dry soil, a soil test can help separate water stress from nutrient stress.",
    ),

    # --- Dataset-driven rules (facts produced by app/dataset.py from
    #     cleaned_crop_recommendation.csv - descriptive ranges, not a model) --
    Rule(
        rule_id="R17",
        name="Temperature above crop's typical range",
        category="dataset",
        conditions=(C("temperature_vs_crop", "above"),),
        conclusions=(("agro_climate", "above_typical"),),
        explanation="The dataset's 10th-90th percentile range for this crop shows the field is hotter than typical.",
    ),
    Rule(
        rule_id="R18",
        name="Conditions outside crop's dataset range",
        category="dataset",
        conditions=(C("crop_ref", "outside"),),
        conclusions=(("agro_climate", "outside_reference"),),
        explanation="One or more readings fall outside the typical dataset range for this crop, so conditions deserve a closer look.",
    ),
    Rule(
        rule_id="R19",
        name="Soil pH outside crop's typical range",
        category="soil_nutrient",
        conditions=(C("ph_ref", "outside"),),
        conclusions=(("soil_advice", "check_ph"),),
        explanation="Soil pH is outside the typical range recorded for this crop in the dataset, which can affect nutrient availability.",
    ),
    Rule(
        rule_id="R20",
        name="Leaf spots in humid air",
        category="leaf_symptoms",
        conditions=(C("symptom", "leaf_spots"), C("humidity_vs_crop", "above")),
        conclusions=(("leaf_diagnosis", "possible_fungal_issue"),),
        explanation="Leaf spots combined with humidity above the crop's typical range often fit fungal problems, which favor moist air.",
    ),
    Rule(
        rule_id="R21",
        name="Hotter than typical plus dry soil",
        category="stress",
        conditions=(C("temperature_vs_crop", "above"), C("soil_moisture", "low")),
        conclusions=(("stress", "heat_and_water"),),
        explanation="Temperature above the dataset's typical range together with dry soil points to heat and water stress.",
    ),
]

# ---------------------------------------------------------------------------
# Human-readable labels for inferred facts (used by the API for the UI)
# ---------------------------------------------------------------------------
ISSUE_LABELS: Dict[str, str] = {
    "water_stress=possible": "Possible water stress (dry soil, no rain)",
    "waterlogging=possible": "Possible waterlogging (wet soil, recent rain)",
    "stress=heat_and_water": "Possible combined heat and water stress",
    "stress=heat_watch": "Heat stress watch (high temperature)",
    "stress=possible_drought_wilting": "Wilting consistent with water shortage",
    "stress=possible_root_issue": "Wilting in wet soil - possible root issue",
    "leaf_diagnosis=possible_underwatering": "Yellowing possibly caused by underwatering",
    "leaf_diagnosis=possible_nutrient_issue": "Yellowing possibly caused by a nutrient issue",
    "leaf_diagnosis=possible_fungal_issue": "Leaf spots possibly fungal/bacterial (wet weather)",
    "leaf_diagnosis=spots_observed": "Leaf spots observed - cause not yet certain",
    "pest_action=scout": "Insect activity detected - scouting recommended",
    "agro_climate=above_typical": "Temperature is above the typical range for this crop (dataset)",
    "agro_climate=outside_reference": "Field conditions are outside the typical dataset range for this crop",
}

RECOMMENDATION_LABELS: Dict[str, str] = {
    "irrigation=needed": "Consider irrigating; water at the root zone early morning or late evening.",
    "irrigation=check_first": "Check soil moisture in the root zone before deciding to irrigate.",
    "irrigation=not_needed": "Skip irrigation for now; the soil is already wet.",
    "soil_advice=improve_drainage": "Inspect field drainage and avoid water standing around plants.",
    "soil_advice=monitor_moisture": "Monitor soil moisture regularly (demo threshold is illustrative only).",
    "soil_advice=rice_prefers_wet": "Keep the soil consistently moist for rice.",
    "soil_advice=consider_soil_test": "Consider a simple soil test to check nutrient status.",
    "soil_advice=check_ph": "Soil pH is outside the typical range for this crop (dataset) - consider a simple soil test.",
    "pest_action=scout": "Scout plants for insects and identify the pest before choosing any control.",
}

# Goals the UI offers for the backward-chaining check.
AVAILABLE_GOALS: List[Tuple[str, str]] = [
    ("irrigation=needed", "Irrigation is needed"),
    ("water_stress=possible", "Water stress is possible"),
    ("stress=heat_and_water", "Heat and water stress is possible"),
    ("leaf_diagnosis=possible_nutrient_issue", "Yellowing may be a nutrient issue"),
    ("pest_action=scout", "Pests should be scouted for"),
    ("soil_advice=improve_drainage", "Soil drainage needs improvement"),
    ("agro_climate=outside_reference", "Conditions are outside the dataset reference"),
    ("soil_advice=check_ph", "Soil pH needs a check"),
]

"""
Tests for the dataset integration (backend/data/*.csv -> descriptive ranges
-> symbolic facts -> IF-THEN rules). No ML is involved anywhere here.

Run from the backend/ directory with:  pytest
"""

from app import dataset
from app.engine import backward_chain, forward_chain
from app.knowledge_base import RULES, normalize_observations


def test_dataset_loads():
    info = dataset.dataset_info()
    assert info["loaded"] is True
    assert info["rows"] == 2200
    assert info["crops"] == 22


def test_crop_specific_reference():
    ref = dataset.reference_for("Rice")
    assert ref["source"] == "crop"
    assert ref["rows"] == 100
    # Rice in this dataset is a warm, wet crop - sanity-check the ranges.
    assert ref["ranges"]["temperature"]["p10"] < ref["ranges"]["temperature"]["p90"]
    assert ref["ranges"]["rainfall"]["p90"] > ref["ranges"]["rainfall"]["p10"]


def test_unknown_crop_falls_back_to_all_crops():
    """Wheat/Tomato are not in the CSV -> all-crop ranges are used."""
    ref = dataset.reference_for("Wheat")
    assert ref["source"] == "all_crops"
    assert ref["rows"] > 0


def test_compare_flags_outside_readings():
    # 55 C is above any crop's typical temperature range.
    out = dataset.compare("Rice", temperature=55, humidity=80, ph=7.0)
    assert ("temperature_vs_crop", "above") in out["facts"]
    assert ("crop_ref", "outside") in out["facts"]
    assert any("Temperature" in d for d in out["deviations"])


def test_compare_accepts_inside_readings():
    ref = dataset.reference_for("Rice")
    # Pick the midpoint of each typical range so the reading is inside it.
    t = (ref["ranges"]["temperature"]["p10"] + ref["ranges"]["temperature"]["p90"]) / 2
    h = (ref["ranges"]["humidity"]["p10"] + ref["ranges"]["humidity"]["p90"]) / 2
    p = (ref["ranges"]["ph"]["p10"] + ref["ranges"]["ph"]["p90"]) / 2
    out = dataset.compare("Rice", temperature=t, humidity=h, ph=p)
    assert ("crop_ref", "inside") in out["facts"]
    assert ("temperature_vs_crop", "typical") in out["facts"]
    assert out["deviations"] == []


def test_forward_chain_fires_dataset_rules():
    """Dataset facts must reach the rule engine and fire R17/R18."""
    ref = dataset.reference_for("Rice")
    hot = ref["ranges"]["temperature"]["p90"] + 5
    facts = normalize_observations(
        crop="Rice", soil_moisture=50, temperature=hot, rainfall="Yes", symptom="None"
    )
    facts.extend(dataset.compare("Rice", temperature=hot, humidity=85, ph=7.0)["facts"])
    result = forward_chain(RULES, facts)

    assert "R17" in result.fired_rules      # temperature above crop range
    assert "R18" in result.fired_rules      # readings outside crop range
    assert ("agro_climate", "above_typical") in result.working_memory


def test_forward_chain_ph_rule():
    facts = normalize_observations(
        crop="Cotton", soil_moisture=50, temperature=25, rainfall="Yes", symptom="None"
    )
    facts.extend(dataset.compare("Cotton", temperature=25, humidity=60, ph=11.5)["facts"])
    result = forward_chain(RULES, facts)
    assert "R19" in result.fired_rules
    assert ("soil_advice", "check_ph") in result.working_memory


def test_backward_chain_proves_dataset_goal():
    ref = dataset.reference_for("Wheat")
    hot = ref["ranges"]["temperature"]["p90"] + 10
    facts = normalize_observations(
        crop="Wheat", soil_moisture=50, temperature=hot, rainfall="Yes", symptom="None"
    )
    facts.extend(dataset.compare("Wheat", temperature=hot, humidity=60, ph=7.0)["facts"])
    result = backward_chain(RULES, facts, "agro_climate=outside_reference")
    assert result.supported is True
    assert any("R18" in line for line in result.proof)

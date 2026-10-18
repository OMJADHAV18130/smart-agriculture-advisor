"""
Sample test cases for the inference engine (forward + backward chaining).

Run from the backend/ directory with:  pytest
"""

from app.engine import Condition as C
from app.engine import Rule, backward_chain, forward_chain
from app.knowledge_base import RULES, normalize_observations


# ---------------------------------------------------------------------------
# FORWARD CHAINING
# ---------------------------------------------------------------------------
def test_forward_dry_soil_no_rain_triggers_irrigation():
    """Dry soil + no rain should fire R01 and R14 (and R06 if hot)."""
    facts = normalize_observations(
        crop="Wheat", soil_moisture=20, temperature=28, rainfall="No", symptom="None"
    )
    result = forward_chain(RULES, facts)

    assert ("irrigation", "needed") in result.working_memory
    assert ("water_stress", "possible") in result.working_memory
    assert "R01" in result.fired_rules
    assert "R14" in result.fired_rules
    # R01 and R14 both fire from the same dry-soil fact -> chain really ran.
    assert len(result.fired_rules) >= 2
    # Every inferred fact must not have been a user fact.
    for fact in result.inferred_facts:
        assert fact not in facts


def test_forward_forward_chaining_fixpoint():
    """Chaining must stop on its own once nothing new is inferred."""
    facts = normalize_observations(
        crop="Tomato", soil_moisture=15, temperature=35, rainfall="No", symptom="Wilting"
    )
    result = forward_chain(RULES, facts)
    # Second run over the same final state must add nothing (idempotent fixpoint).
    second = forward_chain(RULES, result.working_memory)
    assert second.inferred_facts == []
    assert ("stress", "possible_drought_wilting") in result.working_memory
    assert ("stress", "heat_and_water") in result.working_memory


def test_forward_wet_soil_blocks_irrigation_rule():
    """R01 requires rainfall=no; with rain it must NOT fire."""
    facts = normalize_observations(
        crop="Rice", soil_moisture=85, temperature=30, rainfall="Yes", symptom="None"
    )
    result = forward_chain(RULES, facts)
    assert "R01" not in result.fired_rules
    assert ("irrigation", "not_needed") in result.working_memory
    assert "R03" in result.fired_rules
    assert ("soil_advice", "improve_drainage") in result.working_memory  # R04 chained off R03


def test_forward_no_rules_fire_for_normal_conditions():
    facts = normalize_observations(
        crop="Wheat", soil_moisture=55, temperature=25, rainfall="Unknown", symptom="None"
    )
    result = forward_chain(RULES, facts)
    assert result.fired_rules == []


# ---------------------------------------------------------------------------
# BACKWARD CHAINING
# ---------------------------------------------------------------------------
def test_backward_goal_supported_directly():
    facts = normalize_observations(
        crop="Wheat", soil_moisture=20, temperature=28, rainfall="No", symptom="None"
    )
    result = backward_chain(RULES, facts, "irrigation=needed")
    assert result.supported is True
    assert any("R01" in line for line in result.proof)


def test_backward_goal_refuted():
    """With wet soil and recent rain, 'irrigation=needed' is not supported."""
    facts = normalize_observations(
        crop="Rice", soil_moisture=85, temperature=30, rainfall="Yes", symptom="None"
    )
    result = backward_chain(RULES, facts, "irrigation=needed")
    assert result.supported is False


def test_backward_goal_needs_chained_facts():
    """'soil_advice=improve_drainage' depends on 'waterlogging=possible',
    which is itself a conclusion of R03 - a real multi-hop proof."""
    facts = normalize_observations(
        crop="Cotton", soil_moisture=90, temperature=30, rainfall="Yes", symptom="None"
    )
    result = backward_chain(RULES, facts, "soil_advice=improve_drainage")
    assert result.supported is True
    assert any("R04" in line for line in result.proof)
    assert any("R03" in line for line in result.proof)


# ---------------------------------------------------------------------------
# Engine mechanics on a tiny custom knowledge base
# ---------------------------------------------------------------------------
def test_custom_rules_chain_transitively():
    rules = [
        Rule("X1", "a to b", (C("a", "1"),), (("b", "1"),)),
        Rule("X2", "b to c", (C("b", "1"),), (("c", "1"),)),
    ]
    result = forward_chain(rules, [("a", "1")])
    assert result.fired_rules == ["X1", "X2"]
    assert ("c", "1") in result.working_memory


def test_negated_condition_blocks_rule():
    rules = [
        Rule("X1", "needs absence of rain", (C("rain", "yes", negated=True),), (("advice", "go"),)),
    ]
    assert forward_chain(rules, [("rain", "no")]).fired_rules == ["X1"]
    assert forward_chain(rules, [("rain", "yes")]).fired_rules == []


# ---------------------------------------------------------------------------
# Regression: pest rule symptom normalization (bug fix R11)
# ---------------------------------------------------------------------------
def test_forward_insects_leaf_damage_fires_r11():
    """'Insects and Leaf Damage' normalizes to 'insects_and_leaf_damage'.
    R11 must match this fact and infer pest_action=scout.
    Regression guard against the symptom-key mismatch bug.
    """
    facts = normalize_observations(
        crop="Tomato", soil_moisture=50, temperature=28, rainfall="No",
        symptom="Insects and Leaf Damage"
    )
    # Symptom fact must be the underscore version (no 'and' dropped)
    assert ("symptom", "insects_and_leaf_damage") in facts
    result = forward_chain(RULES, facts)
    assert "R11" in result.fired_rules, "R11 (Scout for pests) must fire for insect symptom"
    assert ("pest_action", "scout") in result.inferred_facts

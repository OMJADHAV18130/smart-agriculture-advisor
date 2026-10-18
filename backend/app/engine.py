"""
Inference engine for the Smart Agriculture Advisory Expert System.

This module implements two classic AI search strategies:

1. Forward chaining (data-driven): start from the user's facts and repeatedly
   fire every rule whose conditions are satisfied by the current working
   memory, adding the rule's conclusions to working memory, until no new
   facts can be inferred.

2. Backward chaining (goal-driven): start from a goal fact and work backwards,
   looking for rules that conclude the goal, then trying to prove those
   rules' conditions recursively, until every branch reaches a known fact.

Facts are plain strings such as "soil_moisture=low" or "rainfall=no".
A condition can be a positive fact ("soil_moisture=low") or the absence of
one ("NOT rainfall=recent"). Both are treated as positive literal checks
against working memory; absence checks are written as conditions whose
`expected` value is False.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Fact = Tuple[str, str]  # (key, value) e.g. ("soil_moisture", "low")


@dataclass(frozen=True)
class Condition:
    """A single IF-part atom, e.g. soil_moisture=low or NOT rainfall=recent."""

    key: str
    value: str
    negated: bool = False

    def as_fact(self) -> Fact:
        return (self.key, self.value)

    def matches(self, facts: set) -> bool:
        present = self.as_fact() in facts
        return (not present) if self.negated else present

    def __str__(self) -> str:
        return f"NOT {self.key}={self.value}" if self.negated else f"{self.key}={self.value}"


@dataclass(frozen=True)
class Rule:
    """An IF-THEN production rule."""

    rule_id: str
    name: str
    conditions: Tuple[Condition, ...]
    conclusions: Tuple[Fact, ...]
    explanation: str = ""
    category: str = "general"

    def applicable(self, facts: set) -> bool:
        return all(c.matches(facts) for c in self.conditions)

    def new_conclusions(self, facts: set) -> List[Fact]:
        return [c for c in self.conclusions if c not in facts]

    def __str__(self) -> str:
        ifs = " AND ".join(str(c) for c in self.conditions)
        thens = ", ".join(f"{k}={v}" for k, v in self.conclusions)
        return f"IF {ifs} THEN {thens}"


@dataclass
class ForwardResult:
    """Everything the forward chainer produced, for display to the user."""

    working_memory: List[Fact]
    fired_rules: List[str]            # rule ids in the order they fired
    inferred_facts: List[Fact]        # facts NOT given by the user
    trace: List[str] = field(default_factory=list)  # human-readable steps


def forward_chain(rules: List[Rule], initial_facts: List[Fact],
                  max_cycles: int = 20) -> ForwardResult:
    """Data-driven inference: fire rules until nothing new is learned.

    ``initial_facts`` are the observations supplied by the user. Every fact
    added by a rule is recorded along with which rule added it, so the UI can
    show a readable reasoning trace.
    """
    facts: set = set(initial_facts)
    source: Dict[Fact, str] = {}  # fact -> rule_id that produced it (user facts have no entry)

    trace: List[str] = [f"Start with user facts: {_fmt(initial_facts)}"]
    fired: List[str] = []
    inferred: List[Fact] = []

    for cycle in range(1, max_cycles + 1):
        newly_fired = False
        for rule in rules:
            if not rule.applicable(facts):
                continue
            additions = rule.new_conclusions(facts)
            if not additions:
                continue
            # Fire the rule: record it and add its conclusions.
            fired.append(rule.rule_id)
            trace.append(
                f"Cycle {cycle} - Rule {rule.rule_id} ({rule.name}) fired: "
                f"IF {' AND '.join(str(c) for c in rule.conditions)} "
                f"THEN {', '.join(f'{k}={v}' for k, v in rule.conclusions)}"
            )
            if rule.explanation:
                trace.append(f"    Why: {rule.explanation}")
            for fact in additions:
                facts.add(fact)
                source[fact] = rule.rule_id
                if fact not in initial_facts:
                    inferred.append(fact)
                trace.append(f"    Added fact: {fact[0]}={fact[1]}")
            newly_fired = True
        if not newly_fired:
            trace.append(f"Cycle {cycle}: no more rules apply. Inference stopped.")
            break
    else:
        trace.append(f"Stopped after {max_cycles} cycles (safety limit reached).")

    return ForwardResult(
        working_memory=sorted(facts),
        fired_rules=fired,
        inferred_facts=sorted(inferred),
        trace=trace,
    )


@dataclass
class BackwardResult:
    """Outcome of a goal-driven proof attempt."""

    goal: Fact
    supported: bool
    proof: List[str] = field(default_factory=list)  # human-readable proof tree

    def as_text(self) -> str:
        head = (
            f"Goal {self.goal[0]}={self.goal[1]} is "
            f"{'SUPPORTED' if self.supported else 'NOT supported'} by the current facts."
        )
        return "\n".join([head, *self.proof])


def backward_chain(rules: List[Rule], initial_facts: List[Fact],
                   goal: str, max_depth: int = 15) -> BackwardResult:
    """Goal-driven inference: try to prove a goal from facts and rules.

    ``goal`` is a string like "irrigation=needed". The goal is proved if it is
    already a known fact, or if some rule that concludes the goal can be
    proved. Absence conditions (NOT x=y) are proved when x=y is not known to
    be true. Recursion is bounded by ``max_depth``.
    """
    facts: set = set(initial_facts)
    if "=" not in goal:
        return BackwardResult(
            goal=(goal, "*"),
            supported=False,
            proof=[f"Malformed goal '{goal}'. Use the form key=value."],
        )
    goal_key, goal_value = goal.split("=", 1)
    goal_key, goal_value = goal_key.strip(), goal_value.strip()
    proof: List[str] = []
    supported = _prove(goal_key, goal_value, rules, facts, proof, depth=0, max_depth=max_depth)
    return BackwardResult(goal=(goal_key, goal_value), supported=supported, proof=proof)


def _prove(key: str, value: Optional[str], rules: List[Rule], facts: set,
           proof: List[str], depth: int, max_depth: int) -> bool:
    """Recursively prove that ``key=value`` holds. ``value=None`` means any value."""
    indent = "  " * depth

    if depth > max_depth:
        proof.append(f"{indent}[depth limit reached, giving up on {key}]")
        return False

    # Base case: the fact is already known.
    if value is None:
        known = any(k == key for k, _ in facts)
        known_desc = next((f"{k}={v}" for k, v in facts if k == key), key)
    else:
        known = (key, value) in facts
        known_desc = f"{key}={value}"
    if known:
        proof.append(f"{indent}[fact] {known_desc} is known.")
        return True

    # Recursive case: find rules that could produce this goal.
    for rule in rules:
        for concl_key, concl_value in rule.conclusions:
            if concl_key != key:
                continue
            if value is not None and concl_value != value:
                continue
            proof.append(
                f"{indent}[goal] I need {concl_key}={concl_value} - "
                f"trying Rule {rule.rule_id} ({rule.name})"
            )
            if _prove_conditions(rule, rules, facts, proof, depth + 1, max_depth):
                proof.append(f"{indent}  => Rule {rule.rule_id} holds, "
                             f"so {concl_key}={concl_value} follows.")
                return True
            proof.append(f"{indent}  => Rule {rule.rule_id} could not be proved.")

    # Also allow proving a condition-level atom that a rule merely requires.
    proof.append(f"{indent}No rule could prove {key}={value if value else '*'}.")
    return False


def _prove_conditions(rule: Rule, rules: List[Rule], facts: set,
                      proof: List[str], depth: int, max_depth: int) -> bool:
    """Prove every condition of a rule, one by one."""
    indent = "  " * depth
    ok = True
    for cond in rule.conditions:
        if cond.negated:
            # A NOT condition holds when the fact is not known.
            if cond.as_fact() in facts:
                proof.append(f"{indent}[condition] {cond} is FALSE (fact is known).")
                ok = False
                break
            proof.append(f"{indent}[condition] {cond} holds (fact not known).")
            continue
        if cond.as_fact() in facts:
            proof.append(f"{indent}[condition] {cond} is known.")
            continue
        # Not known directly: try to prove it with other rules.
        if _prove(cond.key, cond.value, rules, facts, proof, depth, max_depth):
            facts.add(cond.as_fact())  # cache the proved fact
            continue
        proof.append(f"{indent}[condition] {cond} could not be proved.")
        ok = False
        break
    return ok


def _fmt(facts: List[Fact]) -> str:
    return ", ".join(f"{k}={v}" for k, v in facts) if facts else "(none)"

"""Object-oriented availability rules used by the MeetPlan scheduler."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    """Public value object returned by every availability rule."""

    accepted: bool
    score: float
    reason: str


class AvailabilityRule(ABC):
    """Base class that encapsulates state matching and scoring behavior."""

    def __init__(self, states: set[str], weight: float) -> None:
        # Private: callers cannot mutate the states owned by a rule.
        self.__states = frozenset(states)
        # Protected: subclasses may use the configured weight.
        self._weight = weight

    @property
    def states(self) -> frozenset[str]:
        """Public, read-only view of the private states."""

        return self.__states

    def matches(self, state: str | None) -> bool:
        """Public template method shared by all rule subclasses."""

        return state in self.__states

    @abstractmethod
    def evaluate(self, state: str | None) -> RuleResult:
        """Evaluate a state; subclasses implement this polymorphically."""


class WeightedAvailabilityRule(AvailabilityRule):
    """Accept an availability state and contribute a configurable score."""

    def __init__(self, state: str, weight: float) -> None:
        super().__init__({state}, weight)
        self.__state = state

    def evaluate(self, state: str | None) -> RuleResult:
        accepted = self.matches(state)
        return RuleResult(
            accepted=accepted,
            score=self._weight if accepted else 0.0,
            reason=f"{self.__state}={self._weight}",
        )


class HardConstraintRule(AvailabilityRule):
    """Reject a slot when a forbidden state is present."""

    def __init__(self, forbidden_state: str) -> None:
        super().__init__({forbidden_state}, 0.0)
        self.__forbidden_state = forbidden_state

    def evaluate(self, state: str | None) -> RuleResult:
        blocked = self.matches(state)
        return RuleResult(
            accepted=not blocked,
            score=0.0,
            reason=f"{self.__forbidden_state}=hard constraint",
        )


class AvailabilityPolicy:
    """Compose rule objects to score a participant state."""

    def __init__(self) -> None:
        self.__hard_constraint = HardConstraintRule("busy")
        self.__scoring_rules: tuple[AvailabilityRule, ...] = (
            WeightedAvailabilityRule("available", 1.0),
            WeightedAvailabilityRule("tentative", 0.5),
        )

    def evaluate(self, state: str | None) -> RuleResult:
        """Apply polymorphic rules and return one normalized result."""

        if state is None:
            return RuleResult(False, 0.0, "missing=unavailable")

        constraint = self.__hard_constraint.evaluate(state)
        if not constraint.accepted:
            return constraint

        for rule in self.__scoring_rules:
            result = rule.evaluate(state)
            if result.accepted:
                return result

        return RuleResult(False, 0.0, f"unknown state: {state}")

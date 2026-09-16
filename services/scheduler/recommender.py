"""Explainable meeting-time ranking for MeetPlan.

The first version deliberately uses deterministic scoring instead of a trained
model. This gives the team an auditable baseline and produces data that can be
used to evaluate a learned ranking model later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


VALID_STATES = {"available", "tentative", "busy"}


@dataclass(frozen=True)
class ParticipantAvailability:
    name: str
    slots: Mapping[str, str]


def _validate(participants: Sequence[ParticipantAvailability]) -> None:
    if not participants:
        raise ValueError("at least one participant is required")

    for participant in participants:
        if not participant.name.strip():
            raise ValueError("participant name cannot be empty")
        invalid = set(participant.slots.values()) - VALID_STATES
        if invalid:
            raise ValueError(
                f"invalid availability state for {participant.name}: "
                f"{', '.join(sorted(invalid))}"
            )


def rank_meeting_slots(
    participants: Sequence[ParticipantAvailability],
    candidate_slots: Iterable[str] | None = None,
) -> list[dict[str, object]]:
    """Rank feasible slots and include an explanation for every score.

    A slot is rejected when any participant marks it ``busy``. Missing input is
    treated as unavailable so a recommendation never assumes consent. Feasible
    slots receive 1 point for ``available`` and 0.5 for ``tentative``.
    """

    _validate(participants)
    slots = set(candidate_slots or ())
    if not slots:
        for participant in participants:
            slots.update(participant.slots)

    ranked: list[dict[str, object]] = []
    for slot in sorted(slots):
        busy = [p.name for p in participants if p.slots.get(slot) == "busy"]
        missing = [p.name for p in participants if slot not in p.slots]
        if busy or missing:
            continue

        available = [
            p.name for p in participants if p.slots.get(slot) == "available"
        ]
        tentative = [
            p.name for p in participants if p.slots.get(slot) == "tentative"
        ]
        raw_score = len(available) + (0.5 * len(tentative))
        normalized_score = raw_score / len(participants)
        ranked.append(
            {
                "slot": slot,
                "score": round(normalized_score, 3),
                "available_count": len(available),
                "tentative_count": len(tentative),
                "explanation": {
                    "available": available,
                    "tentative": tentative,
                    "rule": "available=1.0, tentative=0.5, busy=hard constraint",
                },
            }
        )

    return sorted(
        ranked,
        key=lambda item: (
            -float(item["score"]),
            int(item["tentative_count"]),
            str(item["slot"]),
        ),
    )

"""Validated application layer for the MeetPlan scheduler API."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommender import ParticipantAvailability, rank_meeting_slots


MODEL_VERSION = "deterministic-v1"


def _require_string_list(value: object, field: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must not contain duplicates")
    return value


def recommend_payload(payload: object) -> dict[str, Any]:
    """Validate an API payload and return recommendations with model metadata."""

    if not isinstance(payload, Mapping):
        raise ValueError("request body must be a JSON object")

    raw_participants = payload.get("participants")
    if not isinstance(raw_participants, list) or not raw_participants:
        raise ValueError("participants must be a non-empty list")

    participants: list[ParticipantAvailability] = []
    names: set[str] = set()
    for index, item in enumerate(raw_participants):
        if not isinstance(item, Mapping):
            raise ValueError(f"participants[{index}] must be an object")
        name = item.get("name")
        slots = item.get("slots")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"participants[{index}].name must be a non-empty string")
        normalized_name = name.strip()
        if normalized_name in names:
            raise ValueError("participant names must be unique")
        if not isinstance(slots, Mapping) or not all(
            isinstance(slot, str) and slot.strip() and isinstance(state, str)
            for slot, state in slots.items()
        ):
            raise ValueError(f"participants[{index}].slots must map slot strings to states")
        names.add(normalized_name)
        participants.append(ParticipantAvailability(normalized_name, dict(slots)))

    candidate_slots = _require_string_list(payload.get("candidate_slots"), "candidate_slots")
    recommendations = rank_meeting_slots(participants, candidate_slots)
    return {
        "model_version": MODEL_VERSION,
        "participant_count": len(participants),
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
    }


def readiness_report() -> dict[str, str]:
    """Run a deterministic self-check suitable for a readiness probe."""

    probe = recommend_payload(
        {
            "participants": [
                {"name": "probe-a", "slots": {"probe-slot": "available"}},
                {"name": "probe-b", "slots": {"probe-slot": "tentative"}},
            ]
        }
    )
    expected_score = 0.75
    actual_score = probe["recommendations"][0]["score"]
    if actual_score != expected_score:
        raise RuntimeError(
            f"scheduler self-check failed: expected {expected_score}, got {actual_score}"
        )
    return {"status": "ready", "service": "scheduler", "model_version": MODEL_VERSION}

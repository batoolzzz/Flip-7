"""Shared interface and public observations for Flip 7 agents."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Observation:
    """Information an agent is allowed to use when making a decision."""

    round_score: int
    unique_cards: int
    has_second_chance: bool
    total_score: int
    leader_score: int


class Agent(Protocol):
    name: str

    def choose_action(self, observation: Observation, can_stay: bool = True) -> str:
        """Return either ``hit`` or ``stay``."""


def observe(player, players) -> Observation:
    """Build a fair observation without exposing the shuffled deck."""

    return Observation(
        round_score=player.current_score(),
        unique_cards=player.unique_number_count(),
        has_second_chance=player.has_second_chance,
        total_score=player.total_score,
        leader_score=max(candidate.total_score for candidate in players),
    )

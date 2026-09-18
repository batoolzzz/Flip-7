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
    bust_risk: float = 0.0


class Agent(Protocol):
    name: str

    def choose_action(self, observation: Observation, can_stay: bool = True) -> str:
        """Return either ``hit`` or ``stay``."""


def observe(player, players) -> Observation:
    """Build a fair observation without exposing the shuffled deck."""

    # Flip 7 contains ``n`` copies of number ``n`` (and one zero).  Cards that
    # are already face-up are public information, so Hannah can estimate the
    # chance that her next card duplicates one in her hand without peeking at
    # the shuffled deck.  This matters because a hand containing 10, 11, 12 is
    # much riskier than a hand containing 1, 2, 3 even though both have three
    # unique cards.
    number_copies = {0: 1, **{number: number for number in range(1, 13)}}
    seen_numbers = {number: 0 for number in number_copies}
    visible_card_count = 0
    for candidate in players:
        visible_card_count += len(candidate.display_cards)
        for number in candidate.number_cards:
            seen_numbers[number] += 1

    dangerous_cards = sum(
        max(0, number_copies[number] - seen_numbers[number])
        for number in set(player.number_cards)
    )
    unseen_cards = max(1, 94 - visible_card_count)
    risk = 0.0 if player.has_second_chance else (dangerous_cards / unseen_cards)

    return Observation(
        round_score=player.current_score(),
        unique_cards=player.unique_number_count(),
        has_second_chance=player.has_second_chance,
        total_score=player.total_score,
        leader_score=max(candidate.total_score for candidate in players),
        bust_risk=risk,
    )

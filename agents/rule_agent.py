"""The original hand-written Flip 7 strategy."""

from .base_agent import Observation


class RuleAgent:
    name = "Rule Ranger"

    def choose_action(self, observation: Observation, can_stay: bool = True) -> str:
        if not can_stay:
            return "hit"

        score = observation.round_score
        unique = observation.unique_cards

        if score >= 45:
            return "stay"
        if unique >= 6 and score >= 30:
            return "stay"
        if unique >= 5 and score >= 25:
            return "stay"
        return "hit"

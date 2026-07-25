"""A deliberately simple baseline bot."""

import random

from .base_agent import Observation


class RandomAgent:
    name = "Random Player"

    def choose_action(self, observation: Observation, can_stay: bool = True) -> str:
        if not can_stay:
            return "hit"
        return random.choice(["hit", "stay"])

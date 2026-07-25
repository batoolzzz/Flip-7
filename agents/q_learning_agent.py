"""A small, explainable tabular Q-learning agent."""

import json
import random
from pathlib import Path

from .base_agent import Observation

ACTIONS = ("hit", "stay")


def _bucket(value: int, size: int, maximum: int) -> int:
    return min(value // size, maximum)


class QLearningAgent:
    name = "Self-Play Star"

    def __init__(self, q_table=None, epsilon: float = 0.0):
        self.q_table = q_table if q_table is not None else {}
        self.epsilon = epsilon

    @staticmethod
    def state_key(observation: Observation) -> str:
        """Compress a game observation into a child-readable state."""

        parts = (
            _bucket(observation.round_score, 5, 14),
            observation.unique_cards,
            int(observation.has_second_chance),
        )
        return "|".join(str(part) for part in parts)

    def values(self, observation: Observation) -> dict[str, float]:
        key = self.state_key(observation)
        values = self.q_table.get(key, {})
        return {action: float(values.get(action, 0.0)) for action in ACTIONS}

    def choose_action(self, observation: Observation, can_stay: bool = True) -> str:
        if not can_stay:
            return "hit"
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)

        values = self.values(observation)
        if values["hit"] == values["stay"]:
            return random.choice(ACTIONS)
        return max(ACTIONS, key=values.get)

    def explain(self, observation: Observation, can_stay: bool = True) -> dict:
        values = self.values(observation)
        action = self.choose_action(observation, can_stay)
        return {
            "action": action,
            "hit_value": values["hit"],
            "stay_value": values["stay"],
            "state": self.state_key(observation),
        }

    def update(
        self,
        observation: Observation,
        action: str,
        reward: float,
        next_observation: Observation | None,
        alpha: float = 0.15,
        gamma: float = 0.92,
    ) -> None:
        key = self.state_key(observation)
        row = self.q_table.setdefault(key, {candidate: 0.0 for candidate in ACTIONS})
        future = 0.0
        if next_observation is not None:
            future = max(self.values(next_observation).values())
        target = reward + gamma * future
        row[action] += alpha * (target - row[action])

    def save(self, path: str | Path, metadata: dict | None = None) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"q_table": self.q_table, "metadata": metadata or {}}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, epsilon: float = 0.0):
        path = Path(path)
        if not path.exists():
            return cls(epsilon=epsilon), {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(payload.get("q_table", {}), epsilon), payload.get("metadata", {})

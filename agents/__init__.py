"""Bot strategies used by the Flip 7 game and learning lab."""

from .q_learning_agent import QLearningAgent
from .random_agent import RandomAgent
from .rule_agent import RuleAgent

__all__ = ["QLearningAgent", "RandomAgent", "RuleAgent"]

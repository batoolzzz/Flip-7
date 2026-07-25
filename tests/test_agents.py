import tempfile
import unittest
from pathlib import Path

from agents import QLearningAgent, RandomAgent, RuleAgent
from agents.base_agent import Observation
from training import train_self_play


def observation(score=20, unique=3, second_chance=False):
    return Observation(score, unique, second_chance, 0, 0)


class AgentTests(unittest.TestCase):
    def test_agents_hit_before_staying_is_legal(self):
        for agent in (RandomAgent(), RuleAgent(), QLearningAgent()):
            self.assertEqual(agent.choose_action(observation(), can_stay=False), "hit")

    def test_rule_agent_uses_original_thresholds(self):
        agent = RuleAgent()
        self.assertEqual(agent.choose_action(observation(score=45)), "stay")
        self.assertEqual(agent.choose_action(observation(score=15)), "hit")

    def test_q_update_and_round_trip(self):
        agent = QLearningAgent()
        state = observation(score=25, unique=4)
        agent.update(state, "stay", reward=30, next_observation=None)
        self.assertGreater(agent.values(state)["stay"], 0)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            agent.save(path, {"trained_rounds": 1})
            restored, metadata = QLearningAgent.load(path)
            self.assertEqual(restored.q_table, agent.q_table)
            self.assertEqual(metadata["trained_rounds"], 1)

    def test_self_play_learns_without_baseline_agents(self):
        agent = QLearningAgent()
        history = train_self_play(agent, 20)
        self.assertTrue(agent.q_table)
        self.assertTrue(history)


if __name__ == "__main__":
    unittest.main()

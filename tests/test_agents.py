import tempfile
import unittest
from pathlib import Path

from agents import QLearningAgent, RandomAgent, RuleAgent
from agents.base_agent import Observation
from training import train_self_play
from game import Player, play_freeze, play_flip_three, player_hits
from game.personalization import character_profile, hannah_learning_level


def observation(score=20, unique=3, second_chance=False):
    return Observation(score, unique, second_chance, 0, 0)


class AgentTests(unittest.TestCase):
    def test_hannah_profile_and_learning_levels(self):
        self.assertEqual(character_profile("q_learning")["name"], "Hannah")
        self.assertEqual(character_profile(is_human=True)["subtitle"], "(me)")
        self.assertEqual(hannah_learning_level(0)["level"], 1)
        self.assertEqual(hannah_learning_level(10_000)["level"], 5)
        self.assertEqual(hannah_learning_level(250)["progress"], 0.5)

    def test_human_can_choose_flip_three_target(self):
        human = Player("You", is_human=True)
        hannah = Player("Hannah")
        riley = Player("Riley")
        deck = [
            {"type": "number", "value": 3, "name": "3"},
            {"type": "number", "value": 2, "name": "2"},
            {"type": "number", "value": 1, "name": "1"},
            {"type": "action", "value": "Flip Three", "name": "Flip Three"},
        ]

        player_hits(human, [human, hannah, riley], deck, defer_flip_three=True)
        self.assertTrue(human.pending_flip_three)
        self.assertNotIn("Flip Three", hannah.display_cards)

        play_flip_three(human, hannah, deck)
        self.assertFalse(human.pending_flip_three)
        self.assertEqual(hannah.display_cards, ["Flip Three", "1", "2", "3"])

    def test_bot_flip_three_reports_its_assignment(self):
        hannah = Player("Hannah")
        human = Player("You", is_human=True)
        riley = Player("Riley")
        deck = [
            {"type": "number", "value": 3, "name": "3"},
            {"type": "number", "value": 2, "name": "2"},
            {"type": "number", "value": 1, "name": "1"},
            {"type": "action", "value": "Flip Three", "name": "Flip Three"},
        ]

        log = player_hits(hannah, [hannah, human, riley], deck)
        self.assertTrue(
            any("Hannah: Drew Flip Three and played it on You." in line for line in log)
        )

    def test_human_can_choose_freeze_target(self):
        human = Player("You", is_human=True, number_cards=[8])
        hannah = Player("Hannah", number_cards=[9])
        riley = Player("Riley")
        deck = [
            {"type": "action", "value": "Freeze", "name": "Freeze"},
        ]

        player_hits(
            human,
            [human, hannah, riley],
            deck,
            defer_freeze=True,
        )
        self.assertTrue(human.pending_freeze)
        self.assertTrue(hannah.active)

        log = play_freeze(human, hannah)
        self.assertFalse(human.pending_freeze)
        self.assertFalse(hannah.active)
        self.assertTrue(hannah.frozen)
        self.assertEqual(hannah.current_score(), 9)
        self.assertTrue(any("played it on Hannah" in line for line in log))

    def test_bot_freeze_reports_its_assignment(self):
        hannah = Player("Hannah")
        human = Player("You", is_human=True, number_cards=[8])
        riley = Player("Riley")
        deck = [
            {"type": "action", "value": "Freeze", "name": "Freeze"},
        ]

        log = player_hits(hannah, [hannah, human, riley], deck)
        self.assertFalse(human.active)
        self.assertTrue(
            any("Hannah: Drew Freeze and played it on You." in line for line in log)
        )

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

"""Fast self-play training and evaluation for the tabular agent."""

import random

from agents.base_agent import observe
from agents.q_learning_agent import QLearningAgent
from game import Player, create_deck, player_hits, round_is_over, stay


def _play_round(agents, learning_agent: QLearningAgent | None = None):
    players = [Player(f"Player {index + 1}") for index in range(3)]
    deck = create_deck()
    histories = [[] for _ in players]
    turn = 0

    while not round_is_over(players) and turn < 300:
        index = turn % len(players)
        player = players[index]
        turn += 1
        if not player.active:
            continue

        observation = observe(player, players)
        can_stay = player.has_any_card()
        action = agents[index].choose_action(observation, can_stay)
        histories[index].append((observation, action))

        if action == "stay" and can_stay:
            stay(player)
        else:
            player_hits(player, players, deck)

    scores = [player.current_score() for player in players]
    best_score = max(scores)

    if learning_agent is not None:
        for index, history in enumerate(histories):
            player = players[index]
            terminal_reward = scores[index]
            if player.busted:
                terminal_reward -= 25
            if player.flipped_seven:
                terminal_reward += 20
            if scores.count(best_score) == 1 and scores[index] == best_score:
                terminal_reward += 50

            for position in range(len(history) - 1, -1, -1):
                observation, action = history[position]
                next_observation = (
                    history[position + 1][0]
                    if position + 1 < len(history)
                    else None
                )
                reward = terminal_reward if position == len(history) - 1 else 0.0
                learning_agent.update(observation, action, reward, next_observation)

    return players, scores


def train_self_play(
    agent: QLearningAgent,
    rounds: int,
    starting_round: int = 0,
    epsilon_start: float = 0.8,
    epsilon_end: float = 0.05,
):
    """Train only against copies that share the same evolving Q-table."""

    history = []
    score_window = []
    bust_window = []

    for episode in range(rounds):
        progress = episode / max(1, rounds - 1)
        epsilon = epsilon_start + progress * (epsilon_end - epsilon_start)
        self_players = [QLearningAgent(agent.q_table, epsilon) for _ in range(3)]
        players, scores = _play_round(self_players, learning_agent=agent)
        score_window.extend(scores)
        bust_window.extend(int(player.busted) for player in players)

        checkpoint = max(1, rounds // 20)
        if (episode + 1) % checkpoint == 0 or episode == rounds - 1:
            history.append(
                {
                    "round": starting_round + episode + 1,
                    "average_score": sum(score_window) / len(score_window),
                    "bust_rate": sum(bust_window) / len(bust_window),
                    "states_learned": len(agent.q_table),
                    "epsilon": epsilon,
                }
            )
            score_window = []
            bust_window = []

    agent.epsilon = 0.0
    return history


def evaluate_agent(agent, opponent_factory, rounds: int = 300, seed: int = 7):
    """Evaluate without changing the Q-table."""

    random.seed(seed)
    wins = 0
    total_score = 0
    busts = 0

    for _ in range(rounds):
        opponents = [opponent_factory(), opponent_factory()]
        players, scores = _play_round([agent, *opponents])
        total_score += scores[0]
        busts += int(players[0].busted)
        if scores.count(max(scores)) == 1 and scores[0] == max(scores):
            wins += 1

    return {
        "win_rate": wins / rounds,
        "average_score": total_score / rounds,
        "bust_rate": busts / rounds,
    }

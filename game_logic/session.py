"""
All st.session_state mutations and turn-sequencing logic.
"""

import streamlit as st

from game import (
    Player,
    create_deck,
    play_freeze,
    play_flip_three,
    player_hits,
    round_is_over,
    special_card_pass_message,
    stay,
    winner_if_game_over,
)
from agents import QLearningAgent, RandomAgent, RuleAgent
from agents.base_agent import observe


#  Agent factory 

def make_agent(agent_type: str, model_path):
    if agent_type == "random":
        return RandomAgent()
    if agent_type == "q_learning":
        agent, _ = QLearningAgent.load(model_path)
        return agent
    return RuleAgent()


#  Toast helper 

def queue_special_card_notification(actor, target, card_name: str) -> None:
    icon = ":material/ac_unit:" if card_name == "Freeze" else ":material/style:"
    st.session_state.pending_toast = {
        "body": special_card_pass_message(actor, target, card_name),
        "icon": icon,
    }


def flush_pending_toast() -> None:
    """Call once per render cycle, before any other st.* calls."""
    pending = st.session_state.pop("pending_toast", None)
    if not pending:
        return
    if isinstance(pending, str):
        pending = {"body": pending, "icon": ":material/style:"}
    st.toast(pending["body"], icon=pending["icon"], duration="short")


#  Game initialisation 

def initialize_game(mode: str, agent_options: dict, model_path, character_profile_fn) -> None:
    st.session_state.game_started = True
    st.session_state.mode = mode
    st.session_state.paused = False
    st.session_state.game_over = False
    st.session_state.round_number = 1
    st.session_state.current_player_index = 0
    st.session_state.turn_phase = "thinking"
    st.session_state.pending_round_finish = False
    st.session_state.pending_flip_three_actor_index = None
    st.session_state.pending_freeze_actor_index = None
    st.session_state.deck = create_deck()
    st.session_state.last_ai_explanation = None

    selected_types = [
        agent_options[st.session_state.get("player_1_agent_choice", list(agent_options)[1])],
        agent_options[st.session_state.get("player_2_agent_choice", list(agent_options)[1])],
        agent_options[st.session_state.get("player_3_agent_choice", list(agent_options)[2])],
    ]

    used_names: dict[str, int] = {}
    players = []
    for index, agent_type in enumerate(selected_types):
        is_human = mode == "human" and index == 0
        profile = character_profile_fn(agent_type, is_human=is_human)
        base_name = profile["name"]
        used_names[base_name] = used_names.get(base_name, 0) + 1
        suffix = f" {used_names[base_name]}" if used_names[base_name] > 1 else ""
        players.append(Player(f"{base_name}{suffix}", is_human=is_human))

    st.session_state.players = players
    st.session_state.agent_types = selected_types
    st.session_state.player_agents = [
        None if (mode == "human" and index == 0) else make_agent(agent_type, model_path)
        for index, agent_type in enumerate(selected_types)
    ]
    st.session_state.last_decisions = {p.name: None for p in players}


def reset_everything() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


#  Per-turn helpers 

def current_player():
    return st.session_state.players[st.session_state.current_player_index]


def reset_last_decisions() -> None:
    for player in st.session_state.players:
        st.session_state.last_decisions[player.name] = None


def move_to_next_active_player() -> None:
    players = st.session_state.players
    if round_is_over(players):
        return
    for _ in range(len(players)):
        st.session_state.current_player_index = (
            st.session_state.current_player_index + 1
        ) % len(players)
        if players[st.session_state.current_player_index].active:
            return


def finalize_round() -> None:
    players = st.session_state.players
    for player in players:
        player.total_score += player.current_score()

    if winner_if_game_over(players):
        st.session_state.game_over = True
        st.session_state.paused = True
        return

    st.session_state.round_number += 1
    st.session_state.deck = create_deck()
    for player in players:
        player.reset_round()
    reset_last_decisions()
    st.session_state.current_player_index = 0
    st.session_state.turn_phase = "thinking"
    st.session_state.pending_round_finish = False


def execute_current_turn(decision: str | None = None) -> None:
    if st.session_state.paused or st.session_state.game_over:
        return

    player = current_player()

    if not player.active:
        move_to_next_active_player()
        return

    if decision is None:
        agent = st.session_state.player_agents[st.session_state.current_player_index]
        observation = observe(player, st.session_state.players)
        decision = agent.choose_action(observation, player.has_any_card())
        if isinstance(agent, QLearningAgent):
            st.session_state.last_ai_explanation = {
                "player": player.name,
                **agent.explain(observation, player.has_any_card()),
            }

    if decision == "stay" and player.has_any_card():
        stay(player)
        st.session_state.last_decisions[player.name] = "stay"
    else:
        hit_log = player_hits(
            player,
            st.session_state.players,
            st.session_state.deck,
            defer_flip_three=player.is_human,
            defer_freeze=player.is_human,
        )

        if player.pending_freeze:
            st.session_state.pending_freeze_actor_index = st.session_state.current_player_index
            st.session_state.last_decisions[player.name] = "hit"
            st.session_state.turn_phase = "choosing_freeze"
            return

        if player.pending_flip_three:
            st.session_state.pending_flip_three_actor_index = st.session_state.current_player_index
            st.session_state.last_decisions[player.name] = "hit"
            st.session_state.turn_phase = "choosing_flip_three"
            return

        # Notify for auto-resolved special cards
        flip_three_marker = "Drew Flip Three and played it on "
        assignment = next((e for e in hit_log if flip_three_marker in e), None)
        if assignment and not player.is_human:
            target_name = assignment.split(flip_three_marker, 1)[1].rstrip(".")
            target = next(c for c in st.session_state.players if c.name == target_name)
            queue_special_card_notification(player, target, "Flip Three")

        freeze_marker = "Drew Freeze and played it on "
        freeze_assignment = next((e for e in hit_log if freeze_marker in e), None)
        if freeze_assignment and not player.is_human:
            target_name = freeze_assignment.split(freeze_marker, 1)[1].rstrip(".")
            target = next(c for c in st.session_state.players if c.name == target_name)
            queue_special_card_notification(player, target, "Freeze")

        st.session_state.last_decisions[player.name] = (
            "busted" if player.busted else "hit"
        )

    st.session_state.pending_round_finish = round_is_over(st.session_state.players)
    st.session_state.turn_phase = "result"


def advance_after_result() -> None:
    if st.session_state.pending_round_finish:
        finalize_round()
        return
    reset_last_decisions()
    move_to_next_active_player()
    st.session_state.turn_phase = "thinking"
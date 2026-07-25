import time
import html
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import QLearningAgent, RandomAgent, RuleAgent
from agents.base_agent import Observation, observe
from training import evaluate_agent, train_self_play

from game import (
    Player,
    create_deck,
    player_hits,
    round_is_over,
    stay,
    winner_if_game_over,
)

MODEL_PATH = PROJECT_ROOT / "models" / "q_table.json"
AGENT_OPTIONS = {
    "🎲 Random Rookie": "random",
    "📏 Rule Ranger": "rule",
    "🧠 Self-Play Star": "q_learning",
}

THINK_DELAY_SECONDS = 2
RESULT_DELAY_SECONDS = 2

st.set_page_config(page_title="Flip 7 Demo", layout="wide")

st.markdown(
    """
<style>
* {
    transition: none !important;
    animation: none !important;
}

.stApp {
    background-color: #FFE66D;
}

.stApp,
.stMarkdown,
.stText,
p,
h1,
h2,
h3,
h4,
h5,
h6,
label,
[data-testid="stMarkdownContainer"] {
    color: black !important;
}

div.stButton > button,
div.stButton > button *,
button,
button * {
    color: white !important;
}

div.stButton > button {
    background-color: black;
    color: white;
    border: 2px solid black;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-weight: 700;
}

div.stButton > button:hover {
    background-color: #333333;
    color: white;
    border: 2px solid #333333;
}

[class*="st-key-player_1_hit"] div.stButton > button,
[class*="st-key-player_1_stay"] div.stButton > button {
    background-color: #FFF6BF !important;
    color: black !important;
    border: 3px solid black !important;
    border-radius: 10px !important;
    padding: 8px 22px !important;
    min-height: 47px;
    font-weight: 900 !important;
}

[class*="st-key-player_1_hit"] div.stButton > button *,
[class*="st-key-player_1_stay"] div.stButton > button * {
    color: black !important;
}

[class*="st-key-player_1_hit"] div.stButton > button:hover,
[class*="st-key-player_1_stay"] div.stButton > button:hover {
    background-color: #FFF0A3 !important;
    color: black !important;
    border: 3px solid black !important;
}

[class*="st-key-player_1_stay"] div.stButton > button:disabled {
    background-color: #FFF6BF !important;
    color: black !important;
    border: 3px solid black !important;
    opacity: 0.55;
}

.main-status {
    background-color: white;
    border: 4px solid black;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    font-weight: 900;
    margin-bottom: 12px;
    color: black !important;
}

.round-count {
    color: #CC0000 !important;
    font-size: 30px;
    font-weight: 1000;
    margin-bottom: 12px;
}

.human-controls-area {
    min-height: 95px;
    margin-bottom: 8px;
    text-align: center;
}

.human-controls-title {
    font-size: 22px;
    font-weight: 900;
    color: black !important;
    margin-bottom: 8px;
}

.human-controls-placeholder {
    min-height: 95px;
}

.game-board {
    width: 100%;
    margin-top: 8px;
}

.top-player-row {
    display: flex;
    justify-content: center;
    width: 100%;
}

.bottom-player-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
    margin-top: 14px;
    width: 100%;
}

.player-panel {
    width: 100%;
}

.top-player-row .player-panel {
    max-width: 620px;
}

.player-title {
    text-align: center;
    font-size: 26px;
    font-weight: 900;
    margin-top: 10px;
    margin-bottom: 6px;
    color: black !important;
}

.status-box {
    background-color: white;
    border: 3px solid black;
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    font-weight: 700;
    margin-bottom: 18px;
    color: black !important;
    min-height: 185px;
}

.status-box * {
    color: black !important;
}

.current-player-title {
    color: #008000 !important;
    text-shadow: 0 0 1px #008000;
}

.current-player-box {
    border: 5px solid #008000 !important;
    box-shadow: 0 0 15px rgba(0, 128, 0, 0.6);
}

.turn-label-wrapper {
    text-align: center;
    min-height: 38px;
}

.current-turn-label {
    background-color: #008000;
    color: white !important;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 900;
    display: inline-block;
    margin-bottom: 8px;
}

.player-stats {
    text-align: center;
    color: #2D2755 !important;
    font-size: 16px;
    font-weight: 750;
    line-height: 1.75;
}

.player-stats strong {
    color: #21183F !important;
}

.turn-label-hidden {
    background-color: transparent;
    color: transparent !important;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 900;
    display: inline-block;
    margin-bottom: 8px;
    visibility: hidden;
}

.decision-top-row {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 14px;
    flex-wrap: wrap;
}

.busted-row {
    display: flex;
    justify-content: center;
    margin-top: 12px;
}

.decision-box {
    background-color: #FFF6BF;
    border: 3px solid black;
    border-radius: 10px;
    padding: 8px 22px;
    font-weight: 900;
    min-width: 90px;
    text-align: center;
    color: black !important;
}

.busted-box {
    background-color: #FFF6BF;
    border: 3px solid black;
    border-radius: 10px;
    padding: 9px 28px;
    font-weight: 900;
    min-width: 240px;
    text-align: center;
    color: black !important;
}

.hit-selected {
    border: 5px solid #008000 !important;
    box-shadow: 0 0 10px rgba(0, 128, 0, 0.7);
}

.stay-selected {
    border: 5px solid #CC0000 !important;
    box-shadow: 0 0 10px rgba(204, 0, 0, 0.7);
}

.busted-selected {
    border: 5px solid #CC0000 !important;
    box-shadow: 0 0 10px rgba(204, 0, 0, 0.7);
}

/* Playful board-game theme */
.stApp {
    background:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,.28) 0 5px, transparent 6px),
        radial-gradient(circle at 88% 32%, rgba(255,255,255,.22) 0 7px, transparent 8px),
        linear-gradient(145deg, #6C5CE7 0%, #8A6DE9 48%, #36C5B5 100%);
    background-size: 90px 90px, 130px 130px, auto;
    min-height: 100vh;
}

.block-container {
    max-width: 1180px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.game-logo {
    color: white !important;
    font-family: "Trebuchet MS", Arial, sans-serif;
    font-size: clamp(42px, 7vw, 72px);
    line-height: 1;
    text-align: center;
    font-weight: 1000;
    letter-spacing: -3px;
    text-shadow: 0 5px 0 #3B2A87, 0 9px 18px rgba(30, 20, 80, .28);
    margin: 4px 0 8px;
}

.game-logo-seven {
    color: #FFE66D !important;
}

.game-subtitle {
    color: white !important;
    text-align: center;
    font-size: 17px;
    font-weight: 800;
    margin-bottom: 18px;
}

.main-status {
    background: #FFE66D;
    border: 4px solid #3B2A87;
    border-radius: 24px;
    padding: 12px 20px;
    margin: 0 0 10px;
    box-shadow: 0 7px 0 #3B2A87, 0 12px 22px rgba(30, 20, 80, .22);
}

.round-count {
    color: #3B2A87 !important;
    font-family: "Trebuchet MS", Arial, sans-serif;
    font-size: 28px;
    letter-spacing: 2px;
    margin: 0;
}

div.stButton > button {
    background: #FF6B6B !important;
    color: white !important;
    border: 3px solid #3B2A87 !important;
    border-radius: 14px !important;
    min-height: 48px;
    font-family: "Trebuchet MS", Arial, sans-serif;
    font-weight: 900 !important;
    box-shadow: 0 5px 0 #3B2A87;
    transition: transform .12s ease, box-shadow .12s ease, background .12s ease !important;
}

div.stButton > button:hover {
    background: #FF8585 !important;
    color: white !important;
    border-color: #3B2A87 !important;
    transform: translateY(-2px);
    box-shadow: 0 7px 0 #3B2A87;
}

div.stButton > button:active {
    transform: translateY(3px);
    box-shadow: 0 2px 0 #3B2A87;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, .96);
    border: 4px solid #3B2A87 !important;
    border-radius: 22px !important;
    box-shadow: 0 8px 0 #3B2A87, 0 14px 25px rgba(32, 23, 82, .2);
    padding: 6px;
}

.player-title {
    color: white !important;
    font-family: "Trebuchet MS", Arial, sans-serif;
    font-size: 25px;
    letter-spacing: .5px;
    text-shadow: 0 3px 0 #3B2A87;
    margin-top: 14px;
}

.current-player-title {
    color: #FFE66D !important;
    text-shadow: 0 3px 0 #3B2A87, 0 0 14px rgba(255, 230, 109, .7);
}

.current-turn-label {
    background: #20BF6B;
    border: 3px solid white;
    box-shadow: 0 4px 0 #167D49;
    padding: 7px 16px;
    letter-spacing: 1px;
}

.decision-box,
.busted-box {
    background: #E9E5FF;
    border: 3px solid #3B2A87;
    color: #3B2A87 !important;
    border-radius: 13px;
}

.hit-selected {
    background: #B8F2D0 !important;
    border-color: #16854B !important;
    box-shadow: 0 4px 0 #16854B;
}

.stay-selected {
    background: #FFE69A !important;
    border-color: #D88400 !important;
    box-shadow: 0 4px 0 #D88400;
}

.busted-selected {
    background: #FFD1D1 !important;
    border-color: #D63031 !important;
    box-shadow: 0 4px 0 #D63031;
}

[class*="st-key-player_1_hit"] div.stButton > button,
[class*="st-key-player_1_stay"] div.stButton > button {
    background: #E9E5FF !important;
    color: #3B2A87 !important;
    border: 3px solid #3B2A87 !important;
    box-shadow: 0 4px 0 #3B2A87;
}

[class*="st-key-player_1_hit"] div.stButton > button *,
[class*="st-key-player_1_stay"] div.stButton > button * {
    color: #3B2A87 !important;
}

[class*="st-key-player_1_hit"] div.stButton > button:hover,
[class*="st-key-player_1_stay"] div.stButton > button:hover {
    background: #DCD5FF !important;
    border-color: #3B2A87 !important;
}

@media (max-width: 700px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .game-logo { letter-spacing: -1px; }
    .busted-box { min-width: 170px; }
    .player-title { font-size: 21px; }
}
</style>
""",
    unsafe_allow_html=True,
)


def make_agent(agent_type):
    if agent_type == "random":
        return RandomAgent()
    if agent_type == "q_learning":
        agent, _ = QLearningAgent.load(MODEL_PATH)
        return agent
    return RuleAgent()


def initialize_game(mode):
    st.session_state.game_started = True
    st.session_state.mode = mode
    st.session_state.paused = False
    st.session_state.game_over = False
    st.session_state.round_number = 1
    st.session_state.current_player_index = 0
    st.session_state.turn_phase = "thinking"
    st.session_state.pending_round_finish = False
    st.session_state.deck = create_deck()

    st.session_state.players = [
        Player("Player 1" if mode == "human" else "Player 1 Bot", is_human=(mode == "human")),
        Player("Player 2 Bot"),
        Player("Player 3 Bot"),
    ]

    selected_types = [
        AGENT_OPTIONS[st.session_state.get("player_1_agent_choice", "📏 Rule Ranger")],
        AGENT_OPTIONS[st.session_state.get("player_2_agent_choice", "📏 Rule Ranger")],
        AGENT_OPTIONS[st.session_state.get("player_3_agent_choice", "🧠 Self-Play Star")],
    ]
    st.session_state.player_agents = [
        None if mode == "human" and index == 0 else make_agent(agent_type)
        for index, agent_type in enumerate(selected_types)
    ]
    st.session_state.agent_types = selected_types
    st.session_state.last_ai_explanation = None

    st.session_state.last_decisions = {
        player.name: None for player in st.session_state.players
    }


def reset_everything():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def current_player():
    return st.session_state.players[st.session_state.current_player_index]


def reset_last_decisions():
    for player in st.session_state.players:
        st.session_state.last_decisions[player.name] = None


def move_to_next_active_player():
    players = st.session_state.players

    if round_is_over(players):
        return

    for _ in range(len(players)):
        st.session_state.current_player_index = (
            st.session_state.current_player_index + 1
        ) % len(players)

        if players[st.session_state.current_player_index].active:
            return


def finalize_round():
    players = st.session_state.players

    for player in players:
        points = player.current_score()
        player.total_score += points

    winner = winner_if_game_over(players)

    if winner:
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


def execute_current_turn(decision=None):
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
        player_hits(player, st.session_state.players, st.session_state.deck)

        if player.busted:
            st.session_state.last_decisions[player.name] = "busted"
        else:
            st.session_state.last_decisions[player.name] = "hit"

    st.session_state.pending_round_finish = round_is_over(st.session_state.players)
    st.session_state.turn_phase = "result"


def advance_after_result():
    if st.session_state.pending_round_finish:
        finalize_round()
        return

    reset_last_decisions()
    move_to_next_active_player()
    st.session_state.turn_phase = "thinking"


def get_cards_text(player):
    cards = player.visible_cards()

    if not cards:
        return "None"

    return ", ".join(cards)


def build_player_panel_html(player):
    current = current_player()

    is_current_player = (
        player.name == current.name
        and not st.session_state.game_over
        and (
            player.active
            or st.session_state.turn_phase == "result"
        )
    )

    show_decision_result = (
        is_current_player
        and st.session_state.turn_phase == "result"
    )

    title_class = "player-title current-player-title" if is_current_player else "player-title"
    box_class = "status-box current-player-box" if is_current_player else "status-box"
    turn_label_class = "current-turn-label" if is_current_player else "turn-label-hidden"

    last_decision = st.session_state.last_decisions.get(player.name)

    hit_box_class = (
        "decision-box hit-selected"
        if show_decision_result and last_decision == "hit"
        else "decision-box"
    )

    stay_box_class = (
        "decision-box stay-selected"
        if show_decision_result and last_decision == "stay"
        else "decision-box"
    )

    busted_box_class = (
        "busted-box busted-selected"
        if player.busted
        else "busted-box"
    )

    safe_player_name = html.escape(player.name.upper())
    safe_cards_text = html.escape(get_cards_text(player))

    return (
        f'<div class="player-panel">'
        f'<div class="turn-label-wrapper">'
        f'<span class="{turn_label_class}">CURRENT TURN</span>'
        f'</div>'
        f'<div class="{title_class}">{safe_player_name}</div>'
        f'<div class="{box_class}">'
        f'Total score: {player.total_score}<br>'
        f'Current round score: {player.current_score()}<br>'
        f'Cards: {safe_cards_text}<br>'
        f'<div class="decision-top-row">'
        f'<div class="{hit_box_class}">HIT</div>'
        f'<div class="{stay_box_class}">STAY</div>'
        f'</div>'
        f'<div class="busted-row">'
        f'<div class="{busted_box_class}">BUSTED</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def show_game_board():
    def show_player_panel(player):
        current = current_player()
        is_current = (
            player.name == current.name
            and not st.session_state.game_over
            and (player.active or st.session_state.turn_phase == "result")
        )
        is_human_turn = (
            st.session_state.mode == "human"
            and player.is_human
            and is_current
            and player.active
            and not st.session_state.paused
            and st.session_state.turn_phase == "thinking"
        )

        if is_current:
            st.markdown(
                '<div class="turn-label-wrapper"><span class="current-turn-label">CURRENT TURN</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="turn-label-wrapper"><span class="turn-label-hidden">CURRENT TURN</span></div>',
                unsafe_allow_html=True,
            )

        title_class = "player-title current-player-title" if is_current else "player-title"
        st.markdown(
            f'<div class="{title_class}">{html.escape(player.name.upper())}</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            player_index = st.session_state.players.index(player)
            agent = st.session_state.player_agents[player_index]
            if agent is not None:
                st.caption(f"Bot brain: {agent.name}")
            st.markdown(
                f'<div class="player-stats">'
                f'⭐ Total score: <strong>{player.total_score}</strong><br>'
                f'🎯 This round: <strong>{player.current_score()}</strong><br>'
                f'🃏 Cards: <strong>{html.escape(get_cards_text(player))}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if is_human_turn:
                hit_col, stay_col = st.columns(2)
                with hit_col:
                    if st.button("HIT", key="player_1_hit", use_container_width=True):
                        execute_current_turn("hit")
                        st.rerun()
                with stay_col:
                    if st.button(
                        "STAY",
                        key="player_1_stay",
                        disabled=not player.has_any_card(),
                        use_container_width=True,
                    ):
                        execute_current_turn("stay")
                        st.rerun()
            else:
                last_decision = st.session_state.last_decisions.get(player.name)
                hit_class = "decision-box hit-selected" if is_current and last_decision == "hit" else "decision-box"
                stay_class = "decision-box stay-selected" if is_current and last_decision == "stay" else "decision-box"
                st.markdown(
                    f'<div class="decision-top-row">'
                    f'<div class="{hit_class}">HIT</div>'
                    f'<div class="{stay_class}">STAY</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            if player.busted:
                st.markdown(
                    '<div class="busted-row"><div class="busted-box busted-selected">💥 BUSTED</div></div>',
                    unsafe_allow_html=True,
                )

    top_left, top_center, top_right = st.columns([1, 2, 1])
    with top_center:
        show_player_panel(st.session_state.players[0])

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        show_player_panel(st.session_state.players[2])
    with bottom_right:
        show_player_panel(st.session_state.players[1])


def show_learning_lab():
    agent, metadata = QLearningAgent.load(MODEL_PATH)
    trained_rounds = int(metadata.get("trained_rounds", 0))
    history = list(metadata.get("history", []))

    st.markdown(
        '<div class="main-status"><div class="round-count">🧠 AI LEARNING LAB</div></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "The Self-Play Star learns by playing against copies of itself. "
        "Random Rookie and Rule Ranger are only used afterward to test it."
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Practice rounds", f"{trained_rounds:,}")
    metric_2.metric("Situations learned", f"{len(agent.q_table):,}")
    metric_3.metric("Exploration now", "0% in real games")

    st.subheader("1. Help the bot practise")
    st.write(
        "At first it explores lots of HIT and STAY choices. As it practises, "
        "it explores less and uses the choices that earned better rewards."
    )
    quick_col, deep_col = st.columns(2)
    train_rounds = None
    with quick_col:
        if st.button("⚡ PRACTISE 500 ROUNDS", use_container_width=True):
            train_rounds = 500
    with deep_col:
        if st.button("🚀 PRACTISE 5,000 ROUNDS", use_container_width=True):
            train_rounds = 5000

    if train_rounds:
        with st.spinner("Three Self-Play Stars are practising together..."):
            new_history = train_self_play(
                agent,
                train_rounds,
                starting_round=trained_rounds,
                epsilon_start=0.8 if trained_rounds == 0 else 0.2,
            )
            history.extend(new_history)
            metadata = {
                "trained_rounds": trained_rounds + train_rounds,
                "history": history[-100:],
            }
            agent.save(MODEL_PATH, metadata)
        st.success(f"Finished {train_rounds:,} new self-play rounds!")
        st.rerun()

    if history:
        st.subheader("2. Watch its learning journey")
        chart_data = {
            "Average points": [point["average_score"] for point in history],
            "Bust rate × 100": [point["bust_rate"] * 100 for point in history],
        }
        st.line_chart(chart_data)
        st.caption(
            "The line changes because the opponents are learning too. "
            "That makes self-play harder than memorising one fixed bot."
        )

    st.subheader("3. Test it against the benchmarks")
    if st.button("🏁 RUN A 300-ROUND BOT CHALLENGE", use_container_width=True):
        with st.spinner("Running fair tests without changing what the AI learned..."):
            st.session_state.benchmarks = {
                "Random Rookie": evaluate_agent(agent, RandomAgent),
                "Rule Ranger": evaluate_agent(agent, RuleAgent),
            }

    benchmarks = st.session_state.get("benchmarks")
    if benchmarks:
        columns = st.columns(2)
        for column, (name, result) in zip(columns, benchmarks.items()):
            with column:
                st.metric(f"Win rate vs {name}", f"{result['win_rate']:.0%}")
                st.write(f"Average points: **{result['average_score']:.1f}**")
                st.write(f"Bust rate: **{result['bust_rate']:.0%}**")

    st.subheader("4. Ask what the AI would do")
    explorer_1, explorer_2 = st.columns(2)
    with explorer_1:
        example_score = st.slider("Points this round", 0, 70, 25, 5)
        example_unique = st.slider("Different number cards", 1, 6, 4)
    with explorer_2:
        example_second_chance = st.checkbox("Has a Second Chance")
        st.write("The AI only sees fair, public information—never the hidden deck order.")

    example = Observation(
        round_score=example_score,
        unique_cards=example_unique,
        has_second_chance=example_second_chance,
        total_score=0,
        leader_score=0,
    )
    explanation = agent.explain(example)
    choice = explanation["action"].upper()
    st.success(
        f"The Self-Play Star chooses **{choice}**. "
        f"Learned value — HIT: {explanation['hit_value']:.1f}, "
        f"STAY: {explanation['stay_value']:.1f}."
    )
    if explanation["hit_value"] == explanation["stay_value"] == 0:
        st.warning(
            "This exact kind of situation has not been learned yet. "
            "Give the bot more practice and try again!"
        )


if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "last_decisions" not in st.session_state:
    st.session_state.last_decisions = {}

if "turn_phase" not in st.session_state:
    st.session_state.turn_phase = "thinking"

if "pending_round_finish" not in st.session_state:
    st.session_state.pending_round_finish = False


st.markdown(
    '<div class="game-logo">FLIP <span class="game-logo-seven">7</span></div>'
    '<div class="game-subtitle">Draw cards, dodge duplicates, and race to 200 points!</div>',
    unsafe_allow_html=True,
)

area = st.sidebar.radio("Choose an area", ["🎲 Play", "🧠 Learning Lab"])
if area == "🧠 Learning Lab":
    show_learning_lab()
    st.stop()

if not st.session_state.game_started:
    st.markdown(
        '<div class="main-status"><div class="round-count">CHOOSE YOUR GAME</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="game-subtitle">Take the first seat or sit back and watch the bots battle.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Choose each bot's brain")
    brain_col_1, brain_col_2, brain_col_3 = st.columns(3)
    choices = list(AGENT_OPTIONS)
    with brain_col_1:
        st.selectbox(
            "Player 1 (watch mode)",
            choices,
            index=1,
            key="player_1_agent_choice",
        )
    with brain_col_2:
        st.selectbox(
            "Player 2",
            choices,
            index=1,
            key="player_2_agent_choice",
        )
    with brain_col_3:
        st.selectbox(
            "Player 3",
            choices,
            index=2,
            key="player_3_agent_choice",
        )

    if not MODEL_PATH.exists():
        st.caption(
            "💡 The Self-Play Star is still a beginner. Visit the AI Learning Lab "
            "to give it its first practice rounds."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🤖 WATCH THE BOTS", use_container_width=True):
            initialize_game("automatic")
            st.rerun()

    with col2:
        if st.button("🎮 PLAY YOURSELF", use_container_width=True):
            initialize_game("human")
            st.rerun()

else:
    winner = winner_if_game_over(st.session_state.players)

    center_left, center, center_right = st.columns([1, 2, 1])

    with center:
        st.markdown(
            f'<div class="main-status"><div class="round-count">ROUND {st.session_state.round_number}</div></div>',
            unsafe_allow_html=True,
        )

        button_col1, button_col2 = st.columns(2)

        with button_col1:
            button_text = "▶ RESUME" if st.session_state.paused else "⏸ PAUSE"

            if st.button(button_text, use_container_width=True):
                st.session_state.paused = not st.session_state.paused
                st.rerun()

        with button_col2:
            if st.button("↻ RESTART", use_container_width=True):
                reset_everything()

    if st.session_state.game_over and winner:
        st.success(f"{winner.name} wins the game with {winner.total_score} points!")

    current = current_player()

    show_game_board()

    ai_explanation = st.session_state.get("last_ai_explanation")
    if ai_explanation:
        with st.expander(f"🧠 Why did {ai_explanation['player']} choose that?"):
            st.write(
                f"The Self-Play Star compared its learned values: "
                f"**HIT {ai_explanation['hit_value']:.1f}** and "
                f"**STAY {ai_explanation['stay_value']:.1f}**. "
                f"It chose **{ai_explanation['action'].upper()}** because that choice "
                f"worked better during self-play in similar situations."
            )

    should_auto_think = (
        not st.session_state.paused
        and not st.session_state.game_over
        and st.session_state.turn_phase == "thinking"
        and not (st.session_state.mode == "human" and current.is_human)
    )

    should_auto_advance_result = (
        not st.session_state.paused
        and not st.session_state.game_over
        and st.session_state.turn_phase == "result"
    )

    if should_auto_think:
        time.sleep(THINK_DELAY_SECONDS)
        execute_current_turn()
        st.rerun()

    if should_auto_advance_result:
        time.sleep(RESULT_DELAY_SECONDS)
        advance_after_result()
        st.rerun()

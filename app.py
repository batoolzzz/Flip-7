import time
import html
import streamlit as st

from game import (
    Player,
    bot_decision,
    create_deck,
    player_hits,
    round_is_over,
    stay,
    winner_if_game_over,
)

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
</style>
""",
    unsafe_allow_html=True,
)


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
        Player("Player 1", is_human=(mode == "human")),
        Player("Player 2 Bot"),
        Player("Player 3 Bot"),
    ]

    st.session_state.last_decisions = {
        "Player 1": None,
        "Player 2 Bot": None,
        "Player 3 Bot": None,
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
        decision = bot_decision(player, st.session_state.deck)

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
    player_1_html = build_player_panel_html(st.session_state.players[0])
    player_3_html = build_player_panel_html(st.session_state.players[2])
    player_2_html = build_player_panel_html(st.session_state.players[1])

    board_html = (
        f'<div class="game-board">'
        f'<div class="top-player-row">{player_1_html}</div>'
        f'<div class="bottom-player-row">'
        f'{player_3_html}'
        f'{player_2_html}'
        f'</div>'
        f'</div>'
    )

    st.markdown(board_html, unsafe_allow_html=True)


def show_human_controls(current):
    is_human_turn = (
        st.session_state.mode == "human"
        and current.is_human
        and current.active
        and not st.session_state.paused
        and not st.session_state.game_over
        and st.session_state.turn_phase == "thinking"
    )

    if is_human_turn:
        st.markdown(
            """
<div class="human-controls-area">
    <div class="human-controls-title">Your turn</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Hit"):
                execute_current_turn("hit")
                st.rerun()

        with col2:
            stay_disabled = not current.has_any_card()

            if st.button("Stay", disabled=stay_disabled):
                execute_current_turn("stay")
                st.rerun()

    else:
        st.markdown(
            '<div class="human-controls-placeholder"></div>',
            unsafe_allow_html=True,
        )


if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "last_decisions" not in st.session_state:
    st.session_state.last_decisions = {}

if "turn_phase" not in st.session_state:
    st.session_state.turn_phase = "thinking"

if "pending_round_finish" not in st.session_state:
    st.session_state.pending_round_finish = False


st.title("Flip 7: 3-Player Round Demo")

if not st.session_state.game_started:
    st.write("Choose how Player 1 should play.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Automatic"):
            initialize_game("automatic")
            st.rerun()

    with col2:
        if st.button("Play Yourself"):
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
            button_text = "Resume" if st.session_state.paused else "Pause"

            if st.button(button_text):
                st.session_state.paused = not st.session_state.paused
                st.rerun()

        with button_col2:
            if st.button("Restart Game"):
                reset_everything()

    if st.session_state.game_over and winner:
        st.success(f"{winner.name} wins the game with {winner.total_score} points!")

    current = current_player()

    show_human_controls(current)

    show_game_board()

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
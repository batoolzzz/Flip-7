"""
app.py
------
Streamlit entry point.  This file is ONLY an orchestrator:
  · Initialises session defaults
  · Decides which screen to show
  · Delegates rendering to ui/components.py
  · Delegates state mutations to game_logic/session.py

No HTML strings, no CSS, no game logic lives here.
"""

import time
import sys
from functools import partial
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Domain imports ────────────────────────────────────────────────────────────
from agents import QLearningAgent, RandomAgent, RuleAgent
from training import evaluate_agent, train_self_play
from game.personalization import character_profile, hannah_learning_level
from game import winner_if_game_over

# ── Local layer imports ───────────────────────────────────────────────────────
from ui.components import (
    inject_styles,
    render_logo,
    render_round_banner,
    render_game_controls,
    render_setup_screen,
    render_ai_explanation,
    show_game_board,
    show_learning_lab,
)
from game_logic.session import (
    advance_after_result,
    current_player,
    execute_current_turn,
    flush_pending_toast,
    initialize_game,
    queue_special_card_notification,
    reset_everything,
)
from game import play_freeze, play_flip_three, round_is_over

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_PATH = PROJECT_ROOT / "models" / "q_table.json"

AGENT_OPTIONS = {
    "🎲 Riley (random robot)": "random",
    "📏 Felix (rule-following fox)": "rule",
    "🧠 Hannah (learning AI)": "q_learning",
}

THINK_DELAY_SECONDS = 2
RESULT_DELAY_SECONDS = 2

# ── Page config & global CSS ──────────────────────────────────────────────────
st.set_page_config(page_title="Flip 7 Demo", layout="wide")
inject_styles()

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "game_started": False,
    "last_decisions": {},
    "turn_phase": "thinking",
    "pending_round_finish": False,
    "pending_flip_three_actor_index": None,
    "pending_freeze_actor_index": None,
}
for _key, _value in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value

# ── Flush any queued toast from the previous render cycle ─────────────────────
flush_pending_toast()

# ── Logo ──────────────────────────────────────────────────────────────────────
render_logo()

# ── Sidebar navigation ────────────────────────────────────────────────────────
area = st.sidebar.radio("Choose an area", ["🎲 Play", "🧠 Learning Lab"])

if area == "🧠 Learning Lab":
    agent, metadata = QLearningAgent.load(MODEL_PATH)
    show_learning_lab(
        agent=agent,
        metadata=metadata,
        model_path=MODEL_PATH,
        train_fn=train_self_play,
        evaluate_fn=evaluate_agent,
        random_agent_cls=RandomAgent,
        rule_agent_cls=RuleAgent,
        ql_agent_cls=QLearningAgent,
        observe_fn=None,           # used internally by components.py
        character_profile_fn=character_profile,
        hannah_learning_level_fn=hannah_learning_level,
    )
    st.stop()

# ── Play area ─────────────────────────────────────────────────────────────────
if not st.session_state.game_started:
    render_setup_screen(
        agent_options=AGENT_OPTIONS,
        initialize_game_fn=partial(
            initialize_game,
            agent_options=AGENT_OPTIONS,
            model_path=MODEL_PATH,
            character_profile_fn=character_profile,
        ),
    )
    st.stop()

# ── Active game ───────────────────────────────────────────────────────────────
winner = winner_if_game_over(st.session_state.players)

center_left, center, center_right = st.columns([1, 2, 1])
with center:
    render_round_banner(st.session_state.round_number)
    render_game_controls(reset_fn=reset_everything)

if st.session_state.game_over and winner:
    st.success(f"{winner.name} wins the game with {winner.total_score} points!")

show_game_board(
    execute_turn_fn=execute_current_turn,
    character_profile_fn=character_profile,
)

# ── Special-card dialogs (human only) ─────────────────────────────────────────
if (
    st.session_state.turn_phase == "choosing_freeze"
    and st.session_state.pending_freeze_actor_index is not None
):
    _choose_freeze_target()

if (
    st.session_state.turn_phase == "choosing_flip_three"
    and st.session_state.pending_flip_three_actor_index is not None
):
    _choose_flip_three_target()

render_ai_explanation()

# ── Auto-advance loop ─────────────────────────────────────────────────────────
_current = current_player()

should_auto_think = (
    not st.session_state.paused
    and not st.session_state.game_over
    and st.session_state.turn_phase == "thinking"
    and not (st.session_state.mode == "human" and _current.is_human)
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


# ── Special-card dialog helpers (defined after imports are settled) ────────────
@st.dialog("Choose who gets Flip Three", dismissible=False, icon=":material/style:")
def _choose_flip_three_target():
    actor_index = st.session_state.get("pending_flip_three_actor_index")
    if actor_index is None:
        st.rerun()

    actor = st.session_state.players[actor_index]
    st.write(
        "You drew **Flip Three**. Take the three cards yourself, pass them to "
        "Player 2, or pass them to Player 3. Only active players can receive it."
    )
    for target_index, target in enumerate(st.session_state.players):
        label = (
            f"TAKE THREE CARDS MYSELF — PLAYER {target_index + 1} ({target.name.upper()})"
            if target_index == actor_index
            else f"PASS FLIP THREE TO PLAYER {target_index + 1} ({target.name.upper()})"
        )
        if st.button(label, key=f"flip_three_target_{target_index}",
                     disabled=not target.active, width="stretch"):
            play_flip_three(actor, target, st.session_state.deck)
            queue_special_card_notification(actor, target, "Flip Three")
            st.session_state.pending_flip_three_actor_index = None
            st.session_state.last_decisions[actor.name] = "hit"
            st.session_state.pending_round_finish = round_is_over(st.session_state.players)
            st.session_state.turn_phase = "result"
            st.rerun()


@st.dialog("Choose who gets Freeze", dismissible=False, icon=":material/ac_unit:")
def _choose_freeze_target():
    actor_index = st.session_state.get("pending_freeze_actor_index")
    if actor_index is None:
        st.rerun()

    actor = st.session_state.players[actor_index]
    st.write(
        "You drew **Freeze**. Freeze yourself, pass it to Player 2, or pass it "
        "to Player 3. Only active players can receive it."
    )
    for target_index, target in enumerate(st.session_state.players):
        label = (
            f"FREEZE MYSELF — PLAYER {target_index + 1} ({target.name.upper()})"
            if target_index == actor_index
            else f"PASS FREEZE TO PLAYER {target_index + 1} ({target.name.upper()})"
        )
        if st.button(label, key=f"freeze_target_{target_index}",
                     disabled=not target.active, width="stretch"):
            play_freeze(actor, target)
            queue_special_card_notification(actor, target, "Freeze")
            st.session_state.pending_freeze_actor_index = None
            st.session_state.last_decisions[actor.name] = "hit"
            st.session_state.pending_round_finish = round_is_over(st.session_state.players)
            st.session_state.turn_phase = "result"
            st.rerun()
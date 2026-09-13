"""
This is Streamlit rendering functions used to render state and build HTML string for templates.

"""
from pathlib import Path
import streamlit as st

from ui.templates import (
    html_busted_box,
    html_cards_hand,
    html_choose_game_banner,
    html_compact_header,
    html_decision_boxes,
    html_learning_lab_banner,
    html_player_stats_ribbon,
    html_player_title,
    html_turn_pill,
)

_STYLES_PATH = Path(__file__).parent / "styles.css"


def inject_styles() -> None:
    css = _STYLES_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_compact_cockpit(round_number: int, reset_fn) -> None:
    """Single-row header bar containing Logo, Round number, and controls."""
    bar_col, pause_col, reset_col = st.columns([6, 1.2, 1.2], vertical_alignment="center")
    
    with bar_col:
        st.markdown(html_compact_header(round_number), unsafe_allow_html=True)
        
    with pause_col:
        st.markdown('<div class="cockpit-btn">', unsafe_allow_html=True)
        button_text = "▶ Resume" if st.session_state.paused else "⏸ Pause"
        if st.button(button_text, key="cockpit_pause_btn", use_container_width=True):
            st.session_state.paused = not st.session_state.paused
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with reset_col:
        st.markdown('<div class="cockpit-btn">', unsafe_allow_html=True)
        if st.button("🔄 Restart", key="cockpit_restart_btn", use_container_width=True):
            reset_fn()
        st.markdown('</div>', unsafe_allow_html=True)


def _show_player_panel(player, execute_turn_fn, character_profile_fn) -> None:
    current_index = st.session_state.current_player_index
    players = st.session_state.players
    player_index = players.index(player)

    is_current = (
        player.name == players[current_index].name
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

    # Active glow class wrapper applied directly above the container
    active_class = "active-turn-wrapper" if is_current else "inactive-turn-wrapper"
    st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)

    with st.container(border=True, key=f"player_card_container_{player_index}"):
        st.markdown(html_turn_pill(is_current), unsafe_allow_html=True)

        agent_type = st.session_state.agent_types[player_index]
        profile = character_profile_fn(agent_type, is_human=player.is_human)

        st.markdown(html_player_title(player.name, is_current), unsafe_allow_html=True)

        with st.container(horizontal_alignment="center"):
            st.image(str(profile["avatar"]), width=80)
            st.caption(profile["subtitle"])

        st.markdown(
            html_player_stats_ribbon(player.total_score, player.current_score()),
            unsafe_allow_html=True,
        )

        st.markdown(
            html_cards_hand(player.visible_cards()),
            unsafe_allow_html=True,
        )

        if is_human_turn:
            hit_col, stay_col = st.columns(2)
            with hit_col:
                if st.button("HIT 🎴", key="player_1_hit", use_container_width=True):
                    execute_turn_fn("hit")
                    st.rerun()
            with stay_col:
                if st.button(
                    "STAY 🛑",
                    key="player_1_stay",
                    disabled=not player.has_any_card(),
                    use_container_width=True,
                ):
                    execute_turn_fn("stay")
                    st.rerun()
        else:
            last = st.session_state.last_decisions.get(player.name)
            st.markdown(
                html_decision_boxes(
                    hit_selected=(is_current and last == "hit"),
                    stay_selected=(is_current and last == "stay"),
                ),
                unsafe_allow_html=True,
            )

        if player.busted:
            st.markdown(html_busted_box(is_busted=True), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def show_game_board(execute_turn_fn, character_profile_fn) -> None:
    """
    Renders all 3 players side-by-side in one balanced row.
    Eliminates vertical scrolling completely on desktop screens.
    """
    players = st.session_state.players
    col1, col2, col3 = st.columns(3)

    with col1:
        _show_player_panel(players[0], execute_turn_fn, character_profile_fn)
    with col2:
        _show_player_panel(players[1], execute_turn_fn, character_profile_fn)
    with col3:
        _show_player_panel(players[2], execute_turn_fn, character_profile_fn)


def render_ai_explanation() -> None:
    explanation = st.session_state.get("last_ai_explanation")
    if not explanation:
        return
    with st.expander(f"🧠 Hannah's Brain: Why did {explanation['player']} choose that?"):
        st.write(
            f"Hannah evaluated her learned values: "
            f"**HIT: {explanation['hit_value']:.1f}** vs "
            f"**STAY: {explanation['stay_value']:.1f}**. "
            f"She decided to **{explanation['action'].upper()}** because that choice "
            f"gave her a higher reward during training."
        )


def render_setup_screen(agent_options: dict, initialize_game_fn) -> None:
    st.markdown(html_choose_game_banner(), unsafe_allow_html=True)
    st.markdown("### Choose Bot Personalities")
    brain_col_1, brain_col_2, brain_col_3 = st.columns(3)
    choices = list(agent_options)
    with brain_col_1:
        st.selectbox("Player 1 (watch mode)", choices, index=1, key="player_1_agent_choice")
    with brain_col_2:
        st.selectbox("Player 2", choices, index=1, key="player_2_agent_choice")
    with brain_col_3:
        st.selectbox("Player 3", choices, index=2, key="player_3_agent_choice")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("👀 WATCH THE BOTS", use_container_width=True):
            initialize_game_fn("automatic")
            st.rerun()
    with btn_col2:
        if st.button("🎮 PLAY YOURSELF", use_container_width=True):
            initialize_game_fn("human")
            st.rerun()


def show_learning_lab(
    agent,
    metadata: dict,
    model_path,
    train_fn,
    evaluate_fn,
    random_agent_cls,
    rule_agent_cls,
    ql_agent_cls,
    observe_fn,
    character_profile_fn,
    hannah_learning_level_fn,
) -> None:
    trained_rounds = int(metadata.get("trained_rounds", 0))
    history = list(metadata.get("history", []))
    st.markdown(html_learning_lab_banner(), unsafe_allow_html=True)

    st.info(
        "Hannah learns by playing practice games against copies of herself. "
        "Riley and Felix are only used afterward to test what she learned."
    )
    if st.session_state.pop("training_was_reset", False):
        st.success("Hannah's training was reset. She is starting fresh.")
    learning = hannah_learning_level_fn(trained_rounds)
    intro_portrait, intro_progress = st.columns([1, 3], vertical_alignment="center")
    with intro_portrait:
        st.image(str(character_profile_fn("q_learning")["avatar"]), width=130)
    with intro_progress:
        st.subheader(f"Level {learning['level']}: {learning['title']}")
        progress_text = (
            "Top practice level reached — Hannah can still keep learning!"
            if learning["next_rounds"] is None
            else f"{learning['rounds_to_next']:,} more rounds to reach next level"
        )
        st.progress(learning["progress"], text=progress_text)

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Practice rounds", f"{trained_rounds:,}")
    metric_2.metric("Situations learned", f"{len(agent.q_table):,}")
    metric_3.metric("Exploration now", "0% in real games")

    st.subheader("1. Help Hannah practise")
    st.write(
        "At first Hannah explores lots of HIT and STAY choices. As she practises, "
        "she explores less and uses the choices that earned better rewards."
    )
    quick_col, deep_col = st.columns(2)
    train_rounds = None
    with quick_col:
        if st.button("🚀 PRACTISE 500 ROUNDS", use_container_width=True):
            train_rounds = 500
    with deep_col:
        if st.button("🧠 PRACTISE 5,000 ROUNDS", use_container_width=True):
            train_rounds = 5000

    if train_rounds:
        with st.spinner("Three copies of Hannah are practising together..."):
            new_history = train_fn(agent, train_rounds, starting_round=trained_rounds)
            history.extend(new_history)
            new_metadata = {
                "trained_rounds": trained_rounds + train_rounds,
                "history": history[-100:],
                "model_version": 2,
            }
            agent.save(model_path, new_metadata)
        st.success(f"Finished {train_rounds:,} new self-play rounds!")
        st.rerun()

    with st.expander("Reset AI training"):
        st.warning("This permanently clears Hannah's learned choices and practice history.")
        reset_confirmed = st.checkbox(
            "I understand and want Hannah to start from scratch.",
            key="confirm_training_reset",
        )
        if st.button("RESET AI TRAINING", disabled=not reset_confirmed, use_container_width=True):
            ql_agent_cls().save(
                model_path,
                {"trained_rounds": 0, "history": [], "model_version": 2},
            )
            st.session_state.pop("benchmarks", None)
            st.session_state.training_was_reset = True
            st.rerun()

    if history:
        st.subheader("2. Watch Hannah get smarter")
        st.area_chart(
            history,
            x="round",
            y="states_learned",
            x_label="Practice round",
            y_label="Situations learned",
            color="#028090",
        )
        performance_data = {
            "Hannah's average points": [p["average_score"] for p in history],
            "Hannah's bust rate * 100": [p["bust_rate"] * 100 for p in history],
        }
        st.line_chart(performance_data)

    st.subheader("3. Test Hannah against the other characters")
    if st.button("🏆 RUN A 300-ROUND BOT CHALLENGE", use_container_width=True):
        with st.spinner("Running fair tests without changing what the AI learned..."):
            st.session_state.benchmarks = {
                "Riley": evaluate_fn(agent, random_agent_cls),
                "Felix": evaluate_fn(agent, rule_agent_cls),
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
    from agents.base_agent import Observation
    explorer_1, explorer_2 = st.columns(2)
    with explorer_1:
        example_score = st.slider("Points this round", 0, 70, 25, 5)
        example_unique = st.slider("Different number cards", 1, 6, 4)
    with explorer_2:
        example_second_chance = st.checkbox("Has a Second Chance")
        example_risk = st.slider("Estimated duplicate risk", 0, 50, 15, 5) / 100
    example = Observation(
        round_score=example_score,
        unique_cards=example_unique,
        has_second_chance=example_second_chance,
        total_score=0,
        leader_score=0,
        bust_risk=example_risk,
    )
    explanation = agent.explain(example)
    choice = explanation["action"].upper()
    st.success(
        f"Hannah chooses **{choice}**. "
        f"Learned value — HIT: {explanation['hit_value']:.1f}, "
        f"STAY: {explanation['stay_value']:.1f}."
    )
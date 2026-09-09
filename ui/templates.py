"""
html string builders that return HTML strings for use in Streamlit components.  Used by ui/components.py.
"""

import html as _html

#  Logo & chrome 

def html_logo() -> str:
    return (
        '<div class="game-logo">'
        'FLIP <span class="game-logo-seven">7</span>'
        '</div>'
    )


def html_subtitle(text: str) -> str:
    safe = _html.escape(text)
    return f'<div class="game-subtitle">{safe}</div>'


def html_main_status(inner: str) -> str:
    """Wraps arbitrary content in the branded status banner."""
    return f'<div class="main-status">{inner}</div>'


def html_round_count(label: str) -> str:
    safe = _html.escape(label)
    return f'<div class="round-count">{safe}</div>'


def html_round_banner(round_number: int) -> str:
    return html_main_status(html_round_count(f"ROUND {round_number}"))


def html_choose_game_banner() -> str:
    return html_main_status(html_round_count("CHOOSE YOUR GAME"))


def html_learning_lab_banner() -> str:
    return html_main_status(html_round_count("HANNAH'S LEARNING LAB"))


#  Turn label ─

def html_turn_label(is_current: bool) -> str:
    if is_current:
        return (
            '<div class="turn-label-wrapper">'
            '<span class="current-turn-label">CURRENT TURN</span>'
            '</div>'
        )
    return (
        '<div class="turn-label-wrapper">'
        '<span class="turn-label-hidden">CURRENT TURN</span>'
        '</div>'
    )


#  Player title ─

def html_player_title(name: str, is_current: bool) -> str:
    css = "player-title current-player-title" if is_current else "player-title"
    safe = _html.escape(name.upper())
    return f'<div class="{css}">{safe}</div>'


#  Player stats block ─

def html_player_stats(total_score: int, round_score: int, cards_text: str) -> str:
    safe_cards = _html.escape(cards_text)
    return (
        f'<div class="player-stats">'
        f'⭐ Total score: <strong>{total_score}</strong><br>'
        f'🎯 This round: <strong>{round_score}</strong><br>'
        f'🃏 Cards: <strong>{safe_cards}</strong>'
        f'</div>'
    )


#  Decision boxes ─

def html_decision_boxes(
    hit_selected: bool = False,
    stay_selected: bool = False,
) -> str:
    hit_css = "decision-box hit-selected" if hit_selected else "decision-box"
    stay_css = "decision-box stay-selected" if stay_selected else "decision-box"
    return (
        f'<div class="decision-top-row">'
        f'<div class="{hit_css}">HIT</div>'
        f'<div class="{stay_css}">STAY</div>'
        f'</div>'
    )


def html_busted_box(is_busted: bool) -> str:
    css = "busted-box busted-selected" if is_busted else "busted-box"
    label = "💥 BUSTED" if is_busted else "BUSTED"
    return (
        f'<div class="busted-row">'
        f'<div class="{css}">{label}</div>'
        f'</div>'
    )


#  Full player panel (legacy flat-HTML version, kept for compatibility) ─

def html_player_panel(
    player_name: str,
    total_score: int,
    round_score: int,
    cards_text: str,
    is_current: bool,
    last_decision: str | None,
    is_busted: bool,
    show_decision_result: bool,
) -> str:
    """
    Returns a self-contained player panel as HTML.
    Used when Streamlit containers are not available (e.g. automated watch mode).
    For interactive human-turn panels, use show_player_panel() in components.py
    which renders proper Streamlit widgets.
    """
    title_css = "player-title current-player-title" if is_current else "player-title"
    box_css = "status-box current-player-box" if is_current else "status-box"
    turn_label_css = "current-turn-label" if is_current else "turn-label-hidden"

    hit_css = (
        "decision-box hit-selected"
        if show_decision_result and last_decision == "hit"
        else "decision-box"
    )
    stay_css = (
        "decision-box stay-selected"
        if show_decision_result and last_decision == "stay"
        else "decision-box"
    )
    busted_css = "busted-box busted-selected" if is_busted else "busted-box"

    safe_name = _html.escape(player_name.upper())
    safe_cards = _html.escape(cards_text)

    return (
        f'<div class="player-panel">'
        f'<div class="turn-label-wrapper">'
        f'<span class="{turn_label_css}">CURRENT TURN</span>'
        f'</div>'
        f'<div class="{title_css}">{safe_name}</div>'
        f'<div class="{box_css}">'
        f'Total score: {total_score}<br>'
        f'Current round score: {round_score}<br>'
        f'Cards: {safe_cards}<br>'
        f'<div class="decision-top-row">'
        f'<div class="{hit_css}">HIT</div>'
        f'<div class="{stay_css}">STAY</div>'
        f'</div>'
        f'<div class="busted-row">'
        f'<div class="{busted_css}">BUSTED</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
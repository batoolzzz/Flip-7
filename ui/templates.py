"""
html string builders that return HTML strings for use in Streamlit components.
"""

import html as _html

def html_compact_header(round_number: int, winning_score: int = 200) -> str:
    return (
        f'<div class="top-cockpit-bar">'
        f'  <div class="cockpit-logo-group">'
        f'    <div class="cockpit-logo-text">FLIP <span class="cockpit-logo-seven">7</span></div>'
        f'    <span class="cockpit-round-pill">ROUND {round_number}</span>'
        f'  </div>'
        f'  <div class="cockpit-target-text">First to <strong>{winning_score} pts</strong> wins!</div>'
        f'</div>'
    )


def html_choose_game_banner() -> str:
    return (
        f'<div class="top-cockpit-bar" style="justify-content:center; flex-direction:column; text-align:center; padding: 12px;">'
        f'  <div class="cockpit-logo-text" style="font-size:38px;">FLIP <span class="cockpit-logo-seven">7</span></div>'
        f'  <div style="font-size:14px; font-weight:800; color:#475569; margin-top:4px;">'
        f'    Race to 200 points! Draw cards, dodge duplicates, or bank safe points.'
        f'  </div>'
        f'</div>'
    )


def html_learning_lab_banner() -> str:
    return (
        f'<div class="top-cockpit-bar" style="justify-content:center; text-align:center;">'
        f'  <div class="cockpit-logo-text">HANNAH\'S <span class="cockpit-logo-seven" style="color:#6366F1;">LEARNING LAB</span></div>'
        f'</div>'
    )


def html_turn_pill(is_current: bool) -> str:
    if is_current:
        return '<div class="turn-pill-active">★ YOUR TURN ★</div>'
    return '<div class="turn-pill-inactive">INACTIVE</div>'


def html_player_title(name: str, is_current: bool) -> str:
    css = "player-title active-title" if is_current else "player-title"
    safe = _html.escape(name.upper())
    return f'<div class="{css}">{safe}</div>'


def html_player_stats_ribbon(total_score: int, round_score: int) -> str:
    return (
        f'<div class="compact-score-ribbon">'
        f'  <div class="score-chip">'
        f'    <span class="score-chip-label">Banked</span>'
        f'    <span class="score-chip-num">{total_score}</span>'
        f'  </div>'
        f'  <div class="score-chip">'
        f'    <span class="score-chip-label">This Hand</span>'
        f'    <span class="score-chip-num">{round_score}</span>'
        f'  </div>'
        f'</div>'
    )

def html_card_chip(card_str: str) -> str:
    safe = _html.escape(card_str)
    
    if "Freeze" in card_str:
        return f'<div class="flip7-card card-action-freeze">❄️<br>Freeze</div>'
    if "Flip Three" in card_str:
        return f'<div class="flip7-card card-action-flipthree">⚡<br>Flip 3</div>'
    if "Second Chance" in card_str:
        return f'<div class="flip7-card card-action-secondchance">🛡️<br>Second Chance</div>'
    if card_str.startswith("+") or card_str == "x2":
        return f'<div class="flip7-card card-modifier">{safe}</div>'
    
    return f'<div class="flip7-card card-number">{safe}</div>'


def html_cards_hand(cards: list[str]) -> str:
    if not cards:
        cards_html = '<div class="empty-hand-placeholder">No cards drawn</div>'
    else:
        cards_html = "".join(html_card_chip(c) for c in cards)

    return (
        f'<div class="cards-hand-wrapper">'
        f'  <div class="cards-deck-display">{cards_html}</div>'
        f'</div>'
    )


def html_decision_boxes(hit_selected: bool = False, stay_selected: bool = False) -> str:
    hit_css = "decision-box hit-selected" if hit_selected else "decision-box"
    stay_css = "decision-box stay-selected" if stay_selected else "decision-box"
    return (
        f'<div class="decision-top-row">'
        f'  <div class="{hit_css}">HIT</div>'
        f'  <div class="{stay_css}">STAY</div>'
        f'</div>'
    )


def html_busted_box(is_busted: bool) -> str:
    if not is_busted:
        return ""
    return '<div class="busted-box">BUSTED!</div>'

def html_stayed_box(is_stayed: bool) -> str:
    if not is_stayed:
        return ""
    return '<div class="stayed-box">STAYED!</div>'
import random
from dataclasses import dataclass, field

WINNING_SCORE = 200


@dataclass
class Player:
    name: str
    is_human: bool = False
    number_cards: list[int] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    display_cards: list[str] = field(default_factory=list)
    has_second_chance: bool = False
    active: bool = True
    busted: bool = False
    stayed: bool = False
    frozen: bool = False
    flipped_seven: bool = False
    total_score: int = 0
    last_action: str = "Waiting"

    def reset_round(self):
        self.number_cards = []
        self.modifiers = []
        self.display_cards = []
        self.has_second_chance = False
        self.active = True
        self.busted = False
        self.stayed = False
        self.frozen = False
        self.flipped_seven = False
        self.last_action = "Waiting"

    def visible_cards(self):
        return self.display_cards

    def current_score(self):
        if self.busted:
            return 0

        score = sum(self.number_cards)

        if "x2" in self.modifiers:
            score *= 2

        for modifier in self.modifiers:
            if modifier.startswith("+"):
                score += int(modifier[1:])

        if self.flipped_seven:
            score += 15

        return score

    def unique_number_count(self):
        return len(set(self.number_cards))

    def has_any_card(self):
        return bool(self.display_cards)


def create_deck():
    deck = []

    deck.append({"type": "number", "value": 0, "name": "0"})

    for number in range(1, 13):
        for _ in range(number):
            deck.append({"type": "number", "value": number, "name": str(number)})

    for modifier in ["+2", "+4", "+6", "+8", "+10", "x2"]:
        deck.append({"type": "modifier", "value": modifier, "name": modifier})

    for action in ["Freeze", "Flip Three", "Second Chance"]:
        for _ in range(3):
            deck.append({"type": "action", "value": action, "name": action})

    random.shuffle(deck)
    return deck


def draw_one_card(deck):
    if not deck:
        deck.extend(create_deck())

    return deck.pop()


def bust_risk(player, deck):
    if not deck or player.has_second_chance or not player.number_cards:
        return 0.0

    current_numbers = set(player.number_cards)
    dangerous_cards = 0

    for card in deck:
        if card["type"] == "number" and card["value"] in current_numbers:
            dangerous_cards += 1

    return dangerous_cards / len(deck)


def bot_decision(player, deck):
    if not player.active:
        return "stay"

    if not player.has_any_card():
        return "hit"

    score = player.current_score()
    risk = bust_risk(player, deck)
    unique_cards = player.unique_number_count()

    if score >= 45:
        return "stay"

    if unique_cards >= 6 and score >= 30:
        return "stay"

    if unique_cards >= 5 and score >= 25:
        return "stay"

    if risk >= 0.35 and score >= 18:
        return "stay"

    if risk >= 0.45:
        return "stay"

    return "hit"


def active_players(players):
    return [player for player in players if player.active]


def choose_action_target(players, actor, action_name, deck):
    active = active_players(players)

    if not active:
        return actor

    if len(active) == 1:
        return active[0]

    opponents = [player for player in active if player.name != actor.name]

    if action_name == "Second Chance":
        if not actor.has_second_chance:
            return actor

        for player in active:
            if not player.has_second_chance:
                return player

        return actor

    if action_name == "Freeze":
        if opponents:
            return max(opponents, key=lambda player: player.current_score())
        return actor

    if action_name == "Flip Three":
        if opponents:
            return max(opponents, key=lambda player: bust_risk(player, deck))
        return actor

    return actor


def stay(player):
    player.stayed = True
    player.active = False
    player.last_action = f"Stayed. Score: {player.current_score()}."


def freeze_player(player):
    player.display_cards.append("Freeze")
    player.stayed = True
    player.frozen = True
    player.active = False
    player.last_action = f"Frozen. Score banked: {player.current_score()}."


def give_number_card(player, number):
    player.display_cards.append(str(number))

    if number in player.number_cards:
        if player.has_second_chance:
            player.has_second_chance = False
            player.last_action = (
                f"Drew duplicate {number}, but Second Chance saved them."
            )
            return

        player.busted = True
        player.active = False
        player.last_action = f"Drew duplicate {number}. Bust!"
        return

    player.number_cards.append(number)

    if player.unique_number_count() >= 7:
        player.flipped_seven = True
        player.active = False
        player.last_action = f"Drew {number}. FLIP 7!"
    else:
        player.last_action = f"Drew {number}."


def give_modifier_card(player, modifier):
    player.display_cards.append(modifier)
    player.modifiers.append(modifier)
    player.last_action = f"Drew modifier {modifier}."


def give_second_chance(player):
    player.display_cards.append("Second Chance")

    if not player.has_second_chance:
        player.has_second_chance = True
        player.last_action = "Got Second Chance."
    else:
        player.last_action = "Got extra Second Chance, discarded it."


def apply_card_to_player(player, card):
    if card["type"] == "number":
        give_number_card(player, card["value"])

    elif card["type"] == "modifier":
        give_modifier_card(player, card["value"])


def resolve_flip_three(target, deck, log):
    log.append(f"Flip Three starts for {target.name}.")

    for index in range(3):
        if not target.active:
            break

        card = draw_one_card(deck)

        if card["type"] in ["number", "modifier"]:
            apply_card_to_player(target, card)
            log.append(
                f"{target.name}: Flip Three card {index + 1}: "
                f"{card['name']}. {target.last_action}"
            )

        elif card["value"] == "Second Chance":
            give_second_chance(target)
            log.append(
                f"{target.name}: Flip Three card {index + 1}: "
                f"Second Chance. {target.last_action}"
            )

        elif card["value"] == "Freeze":
            freeze_player(target)
            log.append(
                f"{target.name}: Flip Three card {index + 1}: "
                f"Freeze. {target.last_action}"
            )
            break

        elif card["value"] == "Flip Three":
            target.display_cards.append("Flip Three")
            target.last_action = "Drew extra Flip Three during Flip Three."
            log.append(
                f"{target.name}: Flip Three card {index + 1}: "
                f"Flip Three. {target.last_action}"
            )


def player_hits(player, players, deck):
    log = []

    if not player.active:
        log.append(f"{player.name}: Tried to play but is inactive.")
        return log

    card = draw_one_card(deck)

    if card["type"] in ["number", "modifier"]:
        apply_card_to_player(player, card)
        log.append(f"{player.name}: Hit. Card: {card['name']}. {player.last_action}")
        return log

    action_name = card["value"]
    target = choose_action_target(players, player, action_name, deck)

    if action_name == "Second Chance":
        give_second_chance(target)

        player.last_action = f"Drew Second Chance and gave it to {target.name}."
        log.append(f"{player.name}: {player.last_action}")
        log.append(f"{target.name}: {target.last_action}")

    elif action_name == "Freeze":
        freeze_player(target)

        player.last_action = f"Drew Freeze and played it on {target.name}."
        log.append(f"{player.name}: {player.last_action}")
        log.append(f"{target.name}: {target.last_action}")

    elif action_name == "Flip Three":
        target.display_cards.append("Flip Three")

        player.last_action = f"Drew Flip Three and played it on {target.name}."
        log.append(f"{player.name}: {player.last_action}")
        resolve_flip_three(target, deck, log)

    return log


def round_is_over(players):
    if any(player.flipped_seven for player in players):
        return True

    return all(not player.active for player in players)


def winner_if_game_over(players):
    if any(player.total_score >= WINNING_SCORE for player in players):
        return max(players, key=lambda player: player.total_score)

    return None
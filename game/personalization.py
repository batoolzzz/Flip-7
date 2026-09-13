"""Character profiles and Hannah's learning milestones."""

from pathlib import Path


AVATAR_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "avatars"

CHARACTER_PROFILES = {
    "human": {
        "name": "You",
        "subtitle": "(me)",
        "avatar": AVATAR_DIRECTORY / "player-default.png",
    },
    "q_learning": {
        "name": "Hannah",
        "subtitle": "Learning AI",
        "avatar": AVATAR_DIRECTORY / "hannah.png",
    },
    "random": {
        "name": "Riley",
        "subtitle": "Random robot",
        "avatar": AVATAR_DIRECTORY / "random-robot.png",
    },
    "rule": {
        "name": "Felix",
        "subtitle": "Rule-following fox",
        "avatar": AVATAR_DIRECTORY / "rule-fox.png",
    },
}

# Each milestone is based on genuine completed self-play rounds.
HANNAH_MILESTONES = (
    (0, "Curious beginner"),
    (500, "Card explorer"),
    (2_000, "Pattern spotter"),
    (5_000, "Clever chooser"),
    (10_000, "Strategy star"),
)

# Get Character Profile for player
def character_profile(agent_type: str | None = None, is_human: bool = False) -> dict:
    profile_key = "human" if is_human else agent_type
    return CHARACTER_PROFILES.get(profile_key, CHARACTER_PROFILES["random"])

def hannah_learning_level(trained_rounds: int) -> dict:
    rounds = max(0, int(trained_rounds))
    level_index = 0
    for index, (threshold, _) in enumerate(HANNAH_MILESTONES):
        if rounds >= threshold:
            level_index = index

    threshold, title = HANNAH_MILESTONES[level_index]
    is_top_level = level_index == len(HANNAH_MILESTONES) - 1
    if is_top_level:
        return {
            "level": level_index + 1,
            "title": title,
            "progress": 1.0,
            "next_rounds": None,
            "rounds_to_next": 0,
        }

    next_threshold = HANNAH_MILESTONES[level_index + 1][0]
    progress = (rounds - threshold) / (next_threshold - threshold)
    return {
        "level": level_index + 1,
        "title": title,
        "progress": min(1.0, max(0.0, progress)),
        "next_rounds": next_threshold,
        "rounds_to_next": next_threshold - rounds,
    }

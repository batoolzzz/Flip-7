# Flip 7 Learning Lab

Flip 7 Learning Lab is a small educational Python project that compares three
decision-making strategies in a three-player version of Flip 7:

- **Riley** is a playful robot who chooses randomly.
- **Felix** is a clever fox who follows hand-written score and card-count rules.
- **Hannah** is a learning character who uses a tabular Q-learning policy trained through self-play.

The Streamlit interface lets you play against the characters, watch automated games,
train Hannah, see her learning level and progress graph, benchmark her against the
two baseline agents, and inspect the HIT/STAY values she has learned.

Riley and Felix are evaluation benchmarks. They do not participate in Hannah's
training.

## Project structure

```text
agents/
  base_agent.py         Shared agent protocol and public observation
  random_agent.py       Random HIT/STAY baseline
  rule_agent.py         Hand-written strategy baseline
  q_learning_agent.py   Q-learning policy, updates, explanations, and persistence
game/
  game.py               Deck, player state, scoring, cards, and round rules
  app.py                Streamlit game and AI Learning Lab
training/
  self_play.py          Self-play training and agent evaluation
models/
  q_table.json          Learned Q-values and training metadata
tests/
  test_agents.py        Agent, persistence, and self-play tests
requirements.txt        Python dependencies
```

## How the agents work

Every agent implements:

```python
choose_action(observation, can_stay=True)
```

It returns either `"hit"` or `"stay"`. Agents receive only public information:

- the player's current round score;
- the number of unique number cards they hold;
- whether they have a Second Chance;
- their total game score; and
- the current leader's score.

The Q-learning policy builds its state from the round score, unique card count,
Second Chance status, and an estimated duplicate-card risk based only on public
face-up cards. Scores are grouped into five-point buckets and risk into
five-percentage-point buckets, giving state keys such as `5|4|1|3`: score
bucket 5, four unique cards, an active Second Chance, and risk bucket 3.

During training, three Q-learning agents play against one another while sharing
the same evolving Q-table. Their exploration rate decreases over the run.
Every HIT or STAY in a round learns from that round's final outcome. Terminal
rewards account for round score, flipping seven, and winning the round; a bust
already scores zero and is not penalized a second time. Update sizes and the
exploration rate diminish with experience so later training refines established
choices instead of repeatedly overwriting them. The agent cannot see the
shuffled deck order.

## Set up and run

Create a virtual environment and install the dependency:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

Start the app:

```bash
venv/bin/streamlit run game/app.py
```

Use the sidebar to switch between **Play** and **AI Learning Lab**. In Play mode
you can take the first seat or watch three bots. Games continue until a player
reaches 200 total points.

When you draw **Flip Three**, the game pauses so you can give it to any active
character or take the three cards yourself. Bot assignments appear as a short
on-screen notification.

**Freeze** follows the same targeting rule: the player who draws it chooses any
active character, including themselves. The recipient banks their current-round
points and leaves the round. Bot Freeze assignments also appear as a short
notification.

## Train and evaluate Hannah

Open **AI Learning Lab** in the app to:

1. Run 500 or 5,000 additional self-play rounds.
2. Watch Hannah's level, learned situations, average score, and bust rate change.
3. Run a 300-round benchmark against each baseline agent.
4. Inspect the learned HIT and STAY values for an example situation.

Training saves the updated policy and learning history directly to
`models/q_table.json`. The Learning Lab's reset control clears that file's
learned choices and metadata, so use it carefully.

`training/self_play.py` also exposes `train_self_play()` and `evaluate_agent()`
for use from Python. It is a library module and does not currently have a
standalone command-line interface.

## Run the tests

```bash
venv/bin/python -m unittest discover -s tests -v
```

The tests cover legal first actions, rule-agent thresholds, Q-value updates and
JSON round-tripping, and basic self-play training.

## Saved model format

The model file has two top-level objects:

```json
{
  "q_table": {
    "state-key": {
      "hit": 0.0,
      "stay": 0.0
    }
  },
  "visit_counts": {
    "state-key": {
      "hit": 0,
      "stay": 0
    }
  },
  "metadata": {
    "trained_rounds": 0,
    "history": [],
    "model_version": 2
  }
}
```

Loading a missing model path creates an empty Q-learning agent. For an unseen
state, both actions initially have value zero and the agent breaks the tie
randomly.

## Current limitations and possible improvements

- Self-play and evaluation simulate individual rounds, while the interactive
  app plays complete games to 200 points.
- The game and training code currently assume exactly three players.
- Training does not expose an explicit random seed or configuration file.
- The test suite focuses on agents; the game engine needs broader tests for
  scoring, action cards, round completion, and full-game behavior.
- A future training CLI could expose the learning rate, discount factor,
  exploration schedule, random seed, checkpoint interval, and output path.
- Atomic writes and checkpoint files would make long training runs safer.
- `total_score` and `leader_score` are present in observations but are not yet
  included in the Q-learning state; training currently optimizes round play.

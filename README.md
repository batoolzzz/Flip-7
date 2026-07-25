# Flip 7 Learning Lab

A three-player Streamlit version of Flip 7 that introduces children to
reinforcement learning. Players can compare three different bot brains:

- **Random Rookie** chooses randomly.
- **Rule Ranger** follows hand-written rules.
- **Self-Play Star** uses a Q-table learned only through self-play.

The random and rule-based agents are evaluation benchmarks; they do not teach
the Q-learning agent.

## Run the app

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/streamlit run game/app.py
```

Open **AI Learning Lab** from the sidebar to run more self-play rounds, view the
learning chart, benchmark the trained agent, and explore its HIT/STAY values.

## Run the tests

```bash
venv/bin/python -m unittest discover -s tests
```

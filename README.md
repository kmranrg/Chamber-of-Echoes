# Chamber of Echoes 🐍

**A voice-controlled Snake game powered by Reservoir Computing (RC).**

*"Chamber of Secrets" meets "Echo State Property" — speak to the serpent, and it obeys.*

---

## What Is This?

Chamber of Echoes is a Snake game you play using only your voice. Speak a number into the microphone, and a Reservoir Computing (RC) neural network classifies it into a direction command — no keyboard needed.

| Voice Command | Direction |
|:---:|:---:|
| **8** | UP |
| **2** | DOWN |
| **4** | LEFT |
| **6** | RIGHT |

## How It Works

The reservoir is a randomly initialized recurrent neural network. Input weights (`W_in`) and reservoir weights (`W`) are fixed — only the output layer (`W_out`) is trained via simple linear regression. This makes training fast, lightweight, and energy-efficient compared to traditional deep learning approaches.

## Tech Stack

- **Frontend** — [Flet](https://flet.dev) (Python-based UI framework)
- **ML Model** — Echo State Network (Reservoir Computing)
- **Audio** — Python audio processing for real-time voice capture

## Setup

```bash
git clone https://github.com/kmranrg/Chamber-of-Echoes.git
cd Chamber-of-Echoes
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python game.py
```

**Controls:** Arrow keys / WASD for manual play, Space to start/pause. Voice control activates when the RC controller is connected.

## Project Structure

```
chamber-of-echoes/
├── game.py              # Snake game UI (Flet)
├── rc_controller.py     # RC model
├── requirements.txt
└── README.md
```

## Acknowledgements

Built as a final project for the Reservoir Computing course by [Kumar Anurag](https://kan.phd).

*Named after the Chamber of Secrets from Harry Potter and the Echo State Property from RC theory — because in this game, the serpent listens to your voice.*
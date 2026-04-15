# Chamber of Echoes 🐍

**A voice-controlled Snake game powered by Reservoir Computing (RC).**

*"Chamber of Secrets" meets "Echo State Property" — speak to the serpent, and it obeys.*

---

## What Is This?

Chamber of Echoes is a Snake game you play using only your voice. Speak a number into the microphone, and a Reservoir Computing neural network classifies it into a direction command — no keyboard needed.

| Voice Command | Direction |
|:---:|:---:|
| **8** | ↑ UP |
| **2** | ↓ DOWN |
| **4** | ← LEFT |
| **6** | → RIGHT |

---

## How It Works

```
                    ┌─────────────┐
  Microphone ──────>│ MFCC Feature│
  (1 sec audio)     │ Extraction  │
                    └──────┬──────┘
                           │ 20 coefficients × T timesteps
                           ▼
                 ┌────────────────────────┐
                 │   Reservoir Computing  │
                 │                        │
─── W_in ──────> │  x(k) = (1-α)x(k-1)    │──── W_out ──> Predicted Direction
(random, fixed)  │  + α·tanh(W_in·u(k)    │   (trained)   
                 │  + W·x(k-1))           │
                 │                        │
                 │  100 recurrent neurons │
                 │  with echo state       │
                 │  property              │
                 └────────────────────────┘
                             W
                      (random, fixed)
```

### Reservoir Computing (RC)

RC is a recurrent neural network paradigm where only the output layer is trained. The key insight: a randomly initialized recurrent network (the "reservoir") naturally transforms input signals into a high-dimensional space. A simple linear readout layer learns to extract the desired output from these rich dynamics.

What makes RC special:
- **W_in** (input weights): randomly initialized, never trained
- **W** (reservoir weights): randomly initialized, scaled to satisfy the Echo State Property, never trained
- **W_out** (output weights): the only trainable part — computed via Ridge Regression in a single step (no backpropagation, no gradient descent, no epochs)

### Echo State Property (ESP)

The reservoir weight matrix `W` is scaled so its spectral radius (largest absolute eigenvalue) is slightly below 1.0 (we use 0.95). This ensures the network has a "fading memory" — it remembers recent inputs but gradually forgets older ones, which is exactly what we need for recognizing short audio commands.

### Feature Extraction: MFCCs

Raw audio is converted to Mel-Frequency Cepstral Coefficients (MFCCs) before being fed to the reservoir. MFCCs capture the spectral envelope of speech — essentially a compact representation of "what the voice sounds like" at each moment.

Our pipeline:
1. Record 1 second of audio at 8kHz
2. Trim silence (top_db=20)
3. Pad or crop to exactly 8000 samples
4. Extract 20 MFCCs with FFT window of 512 and hop length of 128
5. Result: a matrix of shape `(T, 20)` where T ≈ 63 timesteps

### Training: Ridge Regression

Instead of iterative optimization, we solve for `W_out` analytically:

```
W_out = Y · R^T · (R · R^T + β · I)^(-1)
```

where `R` is the matrix of reservoir states, `Y` is the target labels, and `β = 0.0001` is a regularization parameter. This gives us the optimal output weights in one computation — no epochs, no learning rate tuning.

---

## Dataset: Free Spoken Digit Dataset (FSDD)

The model is trained on the [Free Spoken Digit Dataset](https://github.com/Jakobovski/free-spoken-digit-dataset), an open dataset of spoken digits (0–9) recorded as `.wav` files at 8kHz.

We filter for only the four digits we need: **2, 4, 6, 8**.

**Data augmentation:** each audio sample is used twice — once clean and once with injected Gaussian white noise (factor=0.005) — to make the model more robust to microphone quality and background noise.

### Record Your Own Voice

For better accuracy with your specific voice and microphone, you can add your own recordings to the training set:

```bash
python record_my_voice.py
```

This will record you saying each digit (2, 4, 6, 8) fifteen times, saving them in FSDD-compatible format (`{digit}_{speaker}_{index}.wav`). After recording, retrain the model:

```bash
rm rc_model.pkl
python rc_controller.py
```

The model will automatically retrain on the combined dataset (FSDD + your recordings) and save a new `rc_model.pkl`.

---

## Project Structure

```
Chamber-of-Echoes/
├── game.py                  # Snake game frontend (Flet)
├── rc.py                    # ReservoirComputer class
├── rc_controller.py         # Audio pipeline + model training/loading
├── record_my_voice.py       # Record your own voice samples
├── rc_model.pkl             # Trained model (auto-generated)
├── requirements.txt
├── assets/
│   └── fonts/
│       └── CinzelDecorative-Bold.ttf
└── dataset/
    └── recordings/          # FSDD .wav files + your recordings
```

| File | Purpose |
|---|---|
| `game.py` | Flet-based Snake game with keyboard + voice control |
| `rc.py` | Core RC implementation: reservoir dynamics, ridge regression training, prediction |
| `rc_controller.py` | End-to-end audio pipeline: MFCC extraction, dataset loading, model train/save/load, microphone recording |
| `record_my_voice.py` | Utility to record your own spoken digit samples for retraining |

---

## Setup

```bash
git clone https://github.com/kmranrg/Chamber-of-Echoes.git
cd Chamber-of-Echoes
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Dependencies

```
flet
numpy
librosa
sounddevice
scikit-learn
scipy
```

---

## Usage

### Play with Keyboard

```bash
python game.py
```

Press **SPACE** to start, use **WASD** or **Arrow Keys** to control the snake.

### Play with Voice

1. Make sure you have a trained model (`rc_model.pkl`). If not, train one:
   ```bash
   python rc_controller.py
   ```

2. Launch the game:
   ```bash
   python game.py
   ```

3. Press **V** to activate voice control. The side panel indicator turns green when listening.

4. Speak **2**, **4**, **6**, or **8** into your microphone. The RC model listens for 1 second, predicts the digit, and sends the corresponding direction to the snake.

5. Press **V** again to turn voice control off.

### Test Voice Recognition Standalone

```bash
python rc_controller.py
```

This runs a loop where you can speak digits and see predictions without the game — useful for checking accuracy.

### Improve Accuracy with Your Voice

```bash
python record_my_voice.py     # Record 15 samples of each digit
rm rc_model.pkl               # Delete old model
python rc_controller.py       # Retrain with your voice included
```

---

## Technical Specs

| Parameter | Value |
|---|---|
| Reservoir size | 100 neurons |
| Spectral radius | 0.95 |
| Leak rate (α) | 0.3 |
| Input dimension | 20 (MFCC coefficients) |
| Output dimension | 4 (digits 2, 4, 6, 8) |
| Regularization (β) | 0.0001 |
| Audio sample rate | 8000 Hz |
| Recording duration | 1.0 second |
| Training method | Ridge Regression (closed-form) |

---

## Why Reservoir Computing?

Traditional deep learning (CNNs, LSTMs, Transformers) would solve this speech classification task with higher accuracy — but at the cost of millions of parameters, GPU training, and significant energy consumption. RC achieves usable accuracy for this 4-class problem with:

- **~100 neurons** (vs millions in deep networks)
- **Zero backpropagation** (single-shot analytical solution)
- **Sub-second training** on CPU
- **Minimal energy footprint**

This project demonstrates that not every AI problem needs a large model — sometimes a small, brain-inspired approach is enough.

---

## Acknowledgements

Built as a final project for the Reservoir Computing course by [Kumar Anurag](https://github.com/kmranrg/Chamber-of-Echoes/blob/main/reference-lecture/L03_Introducing_RC_%5Ba%5D.pdf).

*Named after the Chamber of Secrets from Harry Potter and the Echo State Property from RC theory — because in this game, the serpent listens to your voice.*

import os
import glob
import pickle
import numpy as np
import librosa
import sounddevice as sd
from rc import ReservoirComputer
from sklearn.preprocessing import StandardScaler


DATASET_PATH = "dataset/recordings"
MODEL_FILE = "rc_model.pkl"
SAMPLE_RATE = 8000      # FSDD is sampled at 8kHz
DURATION = 1.0          # 1 second of audio per command

# Mapping numbers to array indices for one-hot encoding
# Index 0 --> '2' (DOWN), Index 1 --> '4' (LEFT), Index 2 --> '6' (RIGHT), Index 3 --> '8' (UP)
TARGET_DIGITS = ['2', '4', '6', '8']

scaler = StandardScaler()   # for normalizing the features

'''
What are MFCCs?

MFCC stands for Mel-frequency Cepstral Coefficients. It’s a feature used in automatic speech and speaker recognition. Essentially, it’s a way to represent the short-term power spectrum of a sound which helps machines understand and process human speech more effectively. Imagine your voice as a unique fingerprint. MFCCs, function similarly to a unique code capturing the salient features of your speech and enabling computers to discern between distinct words, and sounds. In speech recognition applications where computers must translate spoken words into text this code is especially helpful.

Source: https://www.geeksforgeeks.org
'''
def extract_mfcc(audio, sr):
    """Converts raw audio waveform into MFCC features."""
    audio, _ = librosa.effects.trim(audio, top_db=20)

    target_length = int(DURATION * sr)
    if len(audio) < target_length:
        # padding with silence if too short
        audio = np.pad(audio, (0, target_length - len(audio)), mode='constant')
    else:
        # trimming if too long
        audio = audio[:target_length]

    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20, n_fft=512, hop_length=128).T
    return mfccs

def add_noise(audio, noise_factor=0.005):
    """Injects random white noise into the audio signal."""
    noise = np.random.randn(len(audio))
    return audio + noise_factor * noise

def prepare_dataset():
    """Loads FSDD audio files and extract features and labels."""
    X, Y = [], []

    # FSDD format: {digit}_{speaker}_{index}.wav
    search_pattern = os.path.join(DATASET_PATH, "*.wav")
    files = glob.glob(search_pattern)

    if not files:
        raise FileNotFoundError(f"No .wav files found in {DATASET_PATH}")
    
    for file in files:
        filename = os.path.basename(file)
        digit = filename.split('_')[0]

        if digit in TARGET_DIGITS:
            # loading audio
            audio, sr = librosa.load(file, sr=SAMPLE_RATE)

            # extracting features from the clean audio
            features_clean = extract_mfcc(audio, sr)

            # creating a noisy version and extract features
            noisy_audio = add_noise(audio)
            features_noisy = extract_mfcc(noisy_audio, sr)

            # creating one-hot encoded label [0, 0, 0, 0]  --> the first column represents 2, second column represents 4, third column 6 and fourth column 8
            label_idx = TARGET_DIGITS.index(digit)
            one_hot = np.zeros(len(TARGET_DIGITS))
            one_hot[label_idx] = 1.0

            X.append(features_clean)
            Y.append(one_hot)
            X.append(features_noisy)
            Y.append(one_hot)

    X_stacked = np.vstack(X)
    scaler.fit(X_stacked)
    X_scaled = [scaler.transform(seq) for seq in X]

    return X_scaled, Y

def train_and_save_model():
    """Trains the RC network and saves it to a file."""
    print("Extracting features from dataset...")

    X_train, Y_train = prepare_dataset()

    rc = ReservoirComputer(input_dim=20, res_size=100)    # we set input_dim=20 because in we use n_mfcc=20 in extract_mfcc function
    rc.train(X_train, Y_train)

    with open(MODEL_FILE, 'wb') as f:
        pickle.dump({'model': rc, 'scaler': scaler}, f)
    print(f"Model saved to {MODEL_FILE}")
    return rc

def load_model():
    """Loads a pre-trained RC model."""
    global scaler
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, 'rb') as f:
            print("Loaded pre-trained RC model.")
            data = pickle.load(f)
            scaler = data['scaler']
            return data['model']
    else:
        print("No saved model found. Traning from scratch...")
        return train_and_save_model()

def record_and_predict(rc_model):
    """Listens to the microphone for 1 second and predicts the command."""
    print("\nListening for 1 second... Speak now! (2, 4, 6, 8)")

    # recording audio
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait() # wait until recording is finished
    audio = audio.flatten()

    # extracting features and predicting
    features = extract_mfcc(audio, SAMPLE_RATE)
    features_scaled = scaler.transform(features)

    pred_idx = rc_model.predict(features_scaled)

    predicted_digit = TARGET_DIGITS[pred_idx]
    print(f"I heard: {predicted_digit}")
    return predicted_digit

# Test
if __name__ == "__main__":
    model = load_model()

    while True:
        record_and_predict(model)
        val = input("\nPress Enter to test again, or type 'q' to quit: ")
        if val.lower() == 'q':
            break
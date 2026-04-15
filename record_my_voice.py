import sounddevice as sd
import scipy.io.wavfile as wav
import os


DATASET_PATH = 'dataset/recordings'
SAMPLE_RATE = 8000
DURATION = 1.0
MY_NAME = "anurag"

def record_samples(digit, num_samples=15):
    print(f"\nRecording '{digit}'...")
    print(f"Get ready to say '{digit}' {num_samples} times.")
    input("Press Enter to start...")

    for i in range(num_samples):
        print(f"\nRecording {i+1}/{num_samples}.. Speak now!")

        # recording for 1 second
        audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()

        # saving the file in FSDD format
        filename = f"{digit}_{MY_NAME}_{i}.wav"
        filepath = os.path.join(DATASET_PATH, filename)
        wav.write(filepath, SAMPLE_RATE, audio)

        print(f"Saved {filename}")

if __name__ == "__main__":
    if not os.path.exists(DATASET_PATH):
        os.makedirs(DATASET_PATH)

    for target in ['2', '4', '6', '8']:
        record_samples(target, num_samples=15)


    print("\nAll done! Run rc_controller.py to train your model.")

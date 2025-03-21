import librosa
import numpy as np

def compare_with_previous_recordings(username, new_audio_data):
    # Load the last 3 voice samples from storage
    previous_files = [
        f"storage/{username}_1.wav",
        f"storage/{username}_2.wav",
        f"storage/{username}_3.wav"
    ]

    # Convert new audio to a comparable feature vector
    new_audio_features, _ = librosa.load(new_audio_data, sr=16000)
    new_audio_features = np.mean(librosa.feature.mfcc(y=new_audio_features, sr=16000), axis=1)

    # Compare with previous recordings
    matches = 0
    for prev_file in previous_files:
        try:
            prev_audio, _ = librosa.load(prev_file, sr=16000)
            prev_audio_features = np.mean(librosa.feature.mfcc(y=prev_audio, sr=16000), axis=1)

            similarity = np.dot(new_audio_features, prev_audio_features) / (
                    np.linalg.norm(new_audio_features) * np.linalg.norm(prev_audio_features))

            if similarity > 0.85:  # Acceptable voice match threshold
                matches += 1
        except Exception as e:
            print(f"Error comparing audio: {e}")

    return matches >= 2  # Require at least 2 out of 3 matches

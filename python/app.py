from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
from deepfake_proper import DeepfakeDetector
from voice_signature_with_deepfake import transcribe_audio, is_exact_match

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter requests

# Ensure the upload directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Sentences for voice verification
SENTENCES = [
    "Technology is evolving every single day.",
    "The weather today is quite unpredictable.",
    "Artificial intelligence is shaping the future.",
    "Communication is key to building relationships.",
    "A healthy lifestyle requires balance and discipline.",
    "Reading books can expand your knowledge and creativity.",
    "Practice makes progress, not necessarily perfection.",
    "Traveling to new places broadens your perspective.",
    "Learning a new language takes time and dedication.",
    "Every challenge is an opportunity to grow stronger."
]

# Initialize DeepfakeDetector only once
deepfake_detector = DeepfakeDetector("/Users/dhavalbhagat/Desktop/VoicePay/voicepay/python/dataset/shuffled_file.csv")

@app.route("/get_sentences", methods=["GET"])
def get_sentences():
    selected_sentences = random.sample(SENTENCES, 3)
    return jsonify({"sentences": selected_sentences})

@app.route("/verify_speech", methods=["POST"])
def verify_speech():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided", "deepfake_result": "N/A"}), 400
    
    audio = request.files["audio"]
    
    if audio.filename == "":
        return jsonify({"error": "No file selected", "deepfake_result": "N/A"}), 400
    
    expected_text = request.form.get("expected_text", "").strip().lower()

    # Save audio file
    audio_path = os.path.join(UPLOAD_FOLDER, "user_audio5.wav")
    audio.save(audio_path)

    print(f"✅ Received file: {audio.filename}")
    print(f"📌 Saved to: {audio_path}")

    # Check for deepfake
    deepfake_result = deepfake_detector.predict_audio_deepfake(audio_path)  # Call model
    print(f"🔍 Deepfake Detection Result: {deepfake_result}")

    if deepfake_result == "FAKE":
        return jsonify({
            "result": "Deepfake detected",
            "message": "Your voice does not match, possible deepfake detected.",
            "deepfake_result": deepfake_result
        }), 403  # Unauthorized action due to deepfake

    # Transcribe audio
    transcribed_text = transcribe_audio(audio_path)
    if not transcribed_text:
        return jsonify({
            "result": "Could not transcribe",
            "message": "There was an issue processing your audio.",
            "deepfake_result": deepfake_result
        }), 400

    # Check if transcribed text matches expected text
    if is_exact_match(transcribed_text, expected_text):
        return jsonify({
            "result": "Success",
            "message": "Great! Please speak the next sentence.",
            "deepfake_result": deepfake_result
        })
    else:
        return jsonify({
            "result": "Failure",
            "message": "Please speak the correct sentence.",
            "deepfake_result": deepfake_result
        }), 401

if __name__ == "__main__":
    app.run(host="192.168.180.74", port=5001, debug=True)

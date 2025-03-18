from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
from deepfake_proper import DeepfakeDetector
from voice_signature_with_deepfake import transcribe_audio, is_exact_match

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

deepfake_detector = DeepfakeDetector("/Users/dhavalbhagat/Desktop/VoicePay/voicepay/python/dataset/shuffled_file.csv")

user_progress = {}  # Stores user progress (IP-based for simplicity)

@app.route("/get_sentences", methods=["GET"])
def get_sentences():
    selected_sentences = random.sample(SENTENCES, 3)
    user_ip = request.remote_addr
    user_progress[user_ip] = {"sentences": selected_sentences, "index": 0}
    return jsonify({"sentences": selected_sentences})

@app.route("/verify_speech", methods=["POST"])
def verify_speech():
    user_ip = request.remote_addr
    if user_ip not in user_progress:
        return jsonify({"error": "Session expired. Restart required.", "deepfake_result": "N/A"}), 400

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided", "deepfake_result": "N/A"}), 400

    audio = request.files["audio"]
    if audio.filename == "":
        return jsonify({"error": "No file selected", "deepfake_result": "N/A"}), 400

    expected_text = user_progress[user_ip]["sentences"][user_progress[user_ip]["index"]].strip().lower()

    audio_path = os.path.join(UPLOAD_FOLDER, f"user_audio_{user_ip}.wav")
    audio.save(audio_path)

    deepfake_result = deepfake_detector.predict_audio_deepfake(audio_path)

    if deepfake_result == "FAKE":
        del user_progress[user_ip]  # Reset session
        return jsonify({
            "result": "Deepfake detected",
            "message": "Deepfake detected! Restart the process with new sentences.",
            "deepfake_result": deepfake_result
        }), 403
    
    if deepfake_result == "REAL":
        #del user_progress[user_ip]  # Reset session
        return jsonify({
            "result": "Deepfake passed",
            "message": "Deepfake passed!",
            "deepfake_result": deepfake_result
        }), 403
    
    transcribed_text = transcribe_audio(audio_path)
    if not transcribed_text:
        return jsonify({
            "result": "Could not transcribe",
            "message": "Audio processing failed. Please try again.",
            "deepfake_result": deepfake_result
        }), 400

    if not is_exact_match(transcribed_text, expected_text):
        return jsonify({
            "result": "Failure",
            "message": f"❌ Incorrect! Please repeat: \"{expected_text}\"",
            "deepfake_result": deepfake_result
        }), 401

    # Only increment if correct
    user_progress[user_ip]["index"] += 1

    if user_progress[user_ip]["index"] == 3:
        result = {
            "result": "Success",
            "message": "✅ All sentences verified!\n🛡️ Deepfake Check: " + deepfake_result,
            "deepfake_result": deepfake_result,
            "training_complete": True
        }
        del user_progress[user_ip]  # Clear progress after completion
        return jsonify(result)

    return jsonify({
        "result": "Success",
        "message": f"✅ Correct! Please say: \"{user_progress[user_ip]['sentences'][user_progress[user_ip]['index']]}\"",
        "deepfake_result": deepfake_result
    })

if __name__ == "__main__":
    app.run(host="192.168.29.130", port=5001, debug=True)

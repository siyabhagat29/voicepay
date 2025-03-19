from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os
import cloudinary
import cloudinary.uploader
from deepfake_proper import DeepfakeDetector
from voice_signature_with_deepfake import transcribe_audio, is_exact_match
from cryptography.fernet import Fernet
import tempfile

app = Flask(__name__)
CORS(app)

# 🔹 Cloudinary Configuration
cloudinary.config(
    cloud_name="dge7bcso3",
    api_key="681947279915896",
    api_secret="x7dQ49C-PRPIRzQomp_NoEt1NQg"
)

# Sentences for verification
SENTENCES = [
    "Technology is evolving every single day.",
    "The weather today is quite unpredictable.",
    "Artificial intelligence is shaping the future.",
    "A healthy diet leads to a better lifestyle.",
    "Music has the power to change your mood.",
    "Mountains offer breathtaking views and adventures.",
    "Snowfall transforms the landscape beautifully.",
    "Reading daily improves vocabulary and comprehension.",
    "Small acts of kindness can make a big difference.",
    "Social media connects people worldwide.",
    "Blockchain technology ensures secure transactions."
]

deepfake_detector = DeepfakeDetector("/Users/dhavalbhagat/Desktop/VoicePay/voicepay/python/dataset/shuffled_file.csv")

user_progress = {}  # Tracks user verification progress

@app.route("/get_sentences", methods=["POST"])
def get_sentences(): 
    data = request.json
    username = data.get("username")
    
    if not username:
        return jsonify({"error": "Username is required"}), 400

    selected_sentences = random.sample(SENTENCES, 3)
    user_progress[username] = {"sentences": selected_sentences, "index": 0, "audio_files": []}
    
    return jsonify({"sentences": selected_sentences})

def encrypt_audio(file_data):
    """Encrypt audio data using Fernet encryption."""
    encryption_key = Fernet.generate_key()
    cipher = Fernet(encryption_key)
    encrypted_data = cipher.encrypt(file_data)
    return encrypted_data, encryption_key

def upload_to_cloudinary(file_path, filename, resource_type="raw"):
    """Upload a file from disk to Cloudinary."""
    response = cloudinary.uploader.upload(file_path, resource_type=resource_type, public_id=filename, overwrite=True)
    return response["secure_url"]

@app.route("/verify_speech", methods=["POST"])
def verify_speech():
    username = request.form.get("username")
    if username not in user_progress:
        return jsonify({"error": "Session expired. Restart required.", "deepfake_result": "N/A"}), 400

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided", "deepfake_result": "N/A"}), 400

    audio = request.files["audio"]
    file_data = audio.read()  # Read file into memory

    expected_text = user_progress[username]["sentences"][user_progress[username]["index"]].strip().lower()

    # 🔹 Create a temporary audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(file_data)
        temp_audio_path = temp_audio.name  # Save the file path

    try:
        # 🔍 Deepfake detection using temp file
        deepfake_result = deepfake_detector.predict_audio_deepfake(temp_audio_path)
    except Exception as e:
        deepfake_result = f"Error: {str(e)}"

    # 🗑️ Delete the temporary file
    os.remove(temp_audio_path)

    # 🚫 Reject if AI-generated voice detected
    if deepfake_result == "FAKE(AI Voice)":
        del user_progress[username]  # Reset session
        return jsonify({
            "result": "Deepfake detected",
            "message": "🚨 Deepfake detected! Restarting process with new sentences.",
            "deepfake_result": deepfake_result
        }), 403

    # 🎙️ Transcribe the recorded speech
    transcribed_text = transcribe_audio(file_data)
    if not transcribed_text or not is_exact_match(transcribed_text, expected_text):
        return jsonify({
            "result": "Failure",
            "message": f"❌ Incorrect! Please repeat: \"{expected_text}\"",
            "deepfake_result": deepfake_result
        }), 401

    # 🔐 Encrypt the audio file
    encrypted_audio, encryption_key = encrypt_audio(file_data)

    # 🔹 Create temporary files for encrypted audio & encryption key
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as enc_file:
        enc_file.write(encrypted_audio)
        enc_file_path = enc_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as key_file:
        key_file.write(encryption_key)
        key_file_path = key_file.name

    # 🔼 Upload encrypted audio & key to Cloudinary
    enc_filename = f"{username}_{user_progress[username]['index']+1}.enc"
    key_filename = f"{username}_key{user_progress[username]['index']+1}.key"

    cloudinary_audio_url = upload_to_cloudinary(enc_file_path, enc_filename)
    cloudinary_key_url = upload_to_cloudinary(key_file_path, key_filename)

    # 🗑️ Delete temporary encrypted files
    os.remove(enc_file_path)
    os.remove(key_file_path)

    user_progress[username]["audio_files"].append({
        "audio_url": cloudinary_audio_url,
        "key_url": cloudinary_key_url
    })

    # ✅ Success: Move to next sentence
    user_progress[username]["index"] += 1

    if user_progress[username]["index"] == 3:
        result = {
            "result": "Success",
            "message": "✅ All sentences verified!\n🛡️ Deepfake Check: " + deepfake_result,
            "deepfake_result": deepfake_result,
            "training_complete": True,
            "cloudinary_files": user_progress[username]["audio_files"]
        }
        del user_progress[username]  # Clear session after completion
        return jsonify(result)

    return jsonify({
        "result": "Success",
        "message": f"✅ Correct! Next sentence: \"{user_progress[username]['sentences'][user_progress[username]['index']]}\"",
        "deepfake_result": deepfake_result
    })

if __name__ == "__main__":
    app.run(host="192.168.29.130", port=5001, debug=True)

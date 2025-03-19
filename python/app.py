'''from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import cloudinary
import cloudinary.uploader
from deepfake_proper import DeepfakeDetector
from voice_signature_with_deepfake import transcribe_audio, is_exact_match
from cryptography.fernet import Fernet

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Securely generate/store encryption key (DO NOT hardcode in production)
ENCRYPTION_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY)

# 🔹 Cloudinary Configuration (Replace with your credentials)
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

user_progress = {}  # Stores user progress (IP-based)

@app.route("/get_sentences", methods=["GET"])
def get_sentences(): 
    selected_sentences = random.sample(SENTENCES, 3)   # Select sentences randomly
    user_ip = request.remote_addr
    user_progress[user_ip] = {"sentences": selected_sentences, "index": 0, "audio_files": []}
    return jsonify({"sentences": selected_sentences})

def encrypt_audio(file_path):
    """Encrypt audio file using Fernet encryption."""
    with open(file_path, "rb") as file:
        audio_data = file.read()
    encrypted_data = cipher.encrypt(audio_data)

    encrypted_path = file_path + ".enc"
    with open(encrypted_path, "wb") as enc_file:
        enc_file.write(encrypted_data)

    return encrypted_path

def upload_to_cloudinary(file_path):
    """Upload encrypted file to Cloudinary."""
    response = cloudinary.uploader.upload(file_path, resource_type="raw")
    return response["secure_url"]  # Return Cloudinary URL

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

    audio_path = os.path.join(UPLOAD_FOLDER, f"user_audio_{user_ip}_{user_progress[user_ip]['index']}.wav")
    audio.save(audio_path)

    deepfake_result = deepfake_detector.predict_audio_deepfake(audio_path)

    # 🚫 **Reject if AI voice detected**
    if deepfake_result == "FAKE(AI Voice)":
        del user_progress[user_ip]  # Reset session
        return jsonify({
            "result": "Deepfake detected",
            "message": "Deepfake detected! Restart the process with new sentences.",
            "deepfake_result": deepfake_result
        }), 403

    # 🎙️ **Transcribe and verify speech**
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

    # ✅ **If both Deepfake check & speech verification pass, encrypt & upload**
    encrypted_audio_path = encrypt_audio(audio_path)
    cloudinary_url = upload_to_cloudinary(encrypted_audio_path)
    user_progress[user_ip]["audio_files"].append(cloudinary_url)

    # 🔼 Move to next sentence
    user_progress[user_ip]["index"] += 1

    if user_progress[user_ip]["index"] == 3:
        result = {
            "result": "Success",
            "message": "✅ All sentences verified!\n🛡️ Deepfake Check: " + deepfake_result,
            "deepfake_result": deepfake_result,
            "training_complete": True,
            "cloudinary_urls": user_progress[user_ip]["audio_files"]
        }
        del user_progress[user_ip]  # Clear progress after completion
        return jsonify(result)

    return jsonify({
        "result": "Success",
        "message": f"✅ Correct! Please say: \"{user_progress[user_ip]['sentences'][user_progress[user_ip]['index']]}\"",
        "deepfake_result": deepfake_result
    })

if __name__ == "__main__":
    app.run(host="192.168.29.130", port=5001, debug=True)'''













from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os
import cloudinary
import cloudinary.uploader
from deepfake_proper import DeepfakeDetector
from voice_signature_with_deepfake import transcribe_audio, is_exact_match
from cryptography.fernet import Fernet

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

def upload_to_cloudinary(file_data, filename):
    """Upload in-memory file to Cloudinary."""
    response = cloudinary.uploader.upload(file_data, resource_type="raw", public_id=filename, overwrite=True)
    return response["secure_url"]

@app.route("/verify_speech", methods=["POST"])
def verify_speech():
    username = request.form.get("username")
    if username not in user_progress:
        return jsonify({"error": "Session expired. Restart required.", "deepfake_result": "N/A"}), 400

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided", "deepfake_result": "N/A"}), 400

    audio = request.files["audio"]
    file_data = audio.read()  # Read file directly into memory

    expected_text = user_progress[username]["sentences"][user_progress[username]["index"]].strip().lower()

    deepfake_result = deepfake_detector.predict_audio_deepfake(file_data)

    # 🚫 **Reject if AI voice detected**
    if deepfake_result == "FAKE(AI Voice)":
        del user_progress[username]  # Reset session
        return jsonify({
            "result": "Deepfake detected",
            "message": "Deepfake detected! Restart the process with new sentences.",
            "deepfake_result": deepfake_result
        }), 403

    # 🎙️ **Transcribe and verify speech**
    transcribed_text = transcribe_audio(file_data)
    if not transcribed_text or not is_exact_match(transcribed_text, expected_text):
        return jsonify({
            "result": "Failure",
            "message": f"❌ Incorrect! Please repeat: \"{expected_text}\"",
            "deepfake_result": deepfake_result
        }), 401

    # ✅ **Encrypt & upload**
    encrypted_audio, encryption_key = encrypt_audio(file_data)
    enc_filename = f"{username}_{user_progress[username]['index']+1}.enc"
    key_filename = f"{username}_key{user_progress[username]['index']+1}.txt"

    cloudinary_audio_url = upload_to_cloudinary(encrypted_audio, enc_filename)
    cloudinary_key_url = upload_to_cloudinary(encryption_key, key_filename)

    user_progress[username]["audio_files"].append({
        "audio_url": cloudinary_audio_url,
        "key_url": cloudinary_key_url
    })

    # 🔼 Move to next sentence
    user_progress[username]["index"] += 1

    if user_progress[username]["index"] == 3:
        result = {
            "result": "Success",
            "message": "✅ All sentences verified!\n🛡️ Deepfake Check: " + deepfake_result,
            "deepfake_result": deepfake_result,
            "training_complete": True,
            "cloudinary_files": user_progress[username]["audio_files"]
        }
        del user_progress[username]  # Clear progress after completion
        return jsonify(result)

    return jsonify({
        "result": "Success",
        "message": f"✅ Correct! Please say: \"{user_progress[username]['sentences'][user_progress[username]['index']]}\"",
        "deepfake_result": deepfake_result
    })

if __name__ == "__main__":
    app.run(host="192.168.29.130", port=5001, debug=True)



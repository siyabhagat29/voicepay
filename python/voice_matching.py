import librosa
import numpy as np
import os
import io
import tempfile
import requests
from cryptography.fernet import Fernet

def compare_with_previous_recordings(username, new_audio_data):
    print(f"🔹 Comparing voice for user: {username}")
    
    # We need to download the files from Cloudinary
    # Assuming you have a way to list or know the file URLs
    # This is a simplified example - you might need to use Cloudinary's API to list files
    
    encrypted_files = []
    key_files = []
    
    # For demonstration - you should replace with actual Cloudinary API calls
    # to retrieve the URLs for the user's previous recordings
    for i in range(1, 4):  # Get files 1, 2, 3
        encrypted_files.append(f"https://res.cloudinary.com/dge7bcso3/raw/upload/{username}_{i}.enc")
        key_files.append(f"https://res.cloudinary.com/dge7bcso3/raw/upload/{username}_key{i}.txt")
    
    try:
        # Create a temporary file for the new audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            if isinstance(new_audio_data, bytes):
                temp_audio.write(new_audio_data)
                temp_audio_path = temp_audio.name
            else:
                # Assume new_audio_data is already a file path
                temp_audio_path = new_audio_data
        
        # Extract features from new audio
        new_audio_features, _ = librosa.load(temp_audio_path, sr=16000)
        new_audio_features = np.mean(librosa.feature.mfcc(y=new_audio_features, sr=16000), axis=1)
        
        # Clean up temp file
        if isinstance(new_audio_data, bytes):
            os.remove(temp_audio_path)
        
        # Compare with previous recordings from Cloudinary
        matches = 0
        valid_files = 0
        
        for i in range(3):  # Process all 3 pairs of files
            try:
                # Download encrypted audio from Cloudinary
                encrypted_response = requests.get(encrypted_files[i])
                if encrypted_response.status_code != 200:
                    print(f"Failed to download encrypted file: {encrypted_files[i]}")
                    continue
                
                # Download encryption key from Cloudinary
                key_response = requests.get(key_files[i])
                if key_response.status_code != 200:
                    print(f"Failed to download key file: {key_files[i]}")
                    continue
                
                # Decrypt the audio file
                encryption_key = key_response.content
                cipher = Fernet(encryption_key)
                decrypted_audio = cipher.decrypt(encrypted_response.content)
                
                # Save to temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_prev:
                    temp_prev.write(decrypted_audio)
                    prev_file_path = temp_prev.name
                
                # Extract features
                prev_audio, _ = librosa.load(prev_file_path, sr=16000)
                prev_audio_features = np.mean(librosa.feature.mfcc(y=prev_audio, sr=16000), axis=1)
                
                # Calculate similarity
                similarity = np.dot(new_audio_features, prev_audio_features) / (
                        np.linalg.norm(new_audio_features) * np.linalg.norm(prev_audio_features))
                
                print(f"Similarity with previous recording {i+1}: {similarity}")
                
                if similarity > 0.85:  # Acceptable voice match threshold
                    matches += 1
                
                valid_files += 1
                
                # Clean up temp file
                os.remove(prev_file_path)
                
            except Exception as e:
                print(f"Error processing file {i+1}: {e}")
        
        print(f"Total matches: {matches}/{valid_files}")
        
        # Require at least 2 matches if we have at least 2 valid files
        if valid_files >= 2:
            return matches >= 2
        elif valid_files == 1:
            return matches == 1
        else:
            # No valid files to compare against
            print("No valid previous recordings found for comparison")
            return True  # Allow if no previous records (first-time case)
        
    except Exception as e:
        print(f"Error in voice comparison: {e}")
        return False
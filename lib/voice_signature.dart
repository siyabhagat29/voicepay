import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:convert';

class VoiceSignatureScreen extends StatefulWidget {
  const VoiceSignatureScreen({super.key});

  @override
  _VoiceSignatureScreenState createState() => _VoiceSignatureScreenState();
}

class _VoiceSignatureScreenState extends State<VoiceSignatureScreen> {
  String username = "";
  List<String> sentences = [];
  int currentSentenceIndex = 0;
  bool isRecording = false;
  String resultMessage = "Enter your username to start training.";
  final AudioRecorder recorder = AudioRecorder();
  final TextEditingController _usernameController = TextEditingController();
  bool trainingComplete = false;

  @override
  void initState() {
    super.initState();
  }

  Future<void> fetchSentences() async {
    if (username.isEmpty) {
      setState(() {
        resultMessage = "❌ Please enter a username!";
      });
      return;
    }

    try {
      var response = await http.post(
        Uri.parse("http://192.168.29.131:5002/get_sentences"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"username": username}),
      );

      if (response.statusCode == 200) {
        var data = jsonDecode(response.body);
        setState(() {
          sentences = List<String>.from(data["sentences"]);
          resultMessage = "📜 Sentences loaded. Tap to start.";
          currentSentenceIndex = 0;
          trainingComplete = false;
        });
      } else {
        setState(() {
          resultMessage = "❌ Failed to load sentences.";
        });
      }
    } catch (e) {
      setState(() {
        resultMessage = "❌ Error: $e";
      });
    }
  }

  Future<String?> recordAudio() async {
    try {
      if (await recorder.hasPermission()) {
        Directory tempDir = await getTemporaryDirectory();
        String filePath = '${tempDir.path}/audio.wav';

        setState(() {
          resultMessage = "🎤 Recording in progress...";
          isRecording = true;
        });

        await recorder.start(
          const RecordConfig(encoder: AudioEncoder.wav),
          path: filePath,
        );

        await Future.delayed(const Duration(seconds: 5));

        await recorder.stop();
        setState(() {
          isRecording = false;
          resultMessage = "✅ Recording complete. Uploading...";
        });

        return filePath;
      } else {
        setState(() {
          resultMessage = "❌ No microphone permission!";
        });
      }
    } catch (e) {
      setState(() {
        resultMessage = "❌ Recording error: $e";
      });
    }
    return null;
  }

  Future<void> verifySpeech() async {
    if (sentences.isEmpty || username.isEmpty) return;

    setState(() {
      resultMessage = "🎙 Say: \"${sentences[currentSentenceIndex]}\"";
    });

    String? audioFilePath = await recordAudio();
    if (audioFilePath == null) {
      setState(() => resultMessage = "❌ Recording failed.");
      return;
    }

    try {
      var request = http.MultipartRequest(
          "POST", Uri.parse("http://192.168.29.131:5002/verify_speech"));
      request.fields["username"] = username;
      request.files.add(await http.MultipartFile.fromPath("audio", audioFilePath));

      setState(() {
        resultMessage = "📤 Uploading audio...";
      });

      var response = await request.send();
      var responseBody = await response.stream.bytesToString();
      var data = jsonDecode(responseBody);

      String deepfakeResult = data["deepfake_result"] ?? "Unknown";
      String message = data["message"] ?? "Unknown response";

      if (response.statusCode == 403) { // Deepfake detected
        setState(() {
          resultMessage = "🚨 Deepfake detected! Restarting process.\n🛡️ Deepfake Check: $deepfakeResult";
        });
        await Future.delayed(const Duration(seconds: 3));
        fetchSentences();
        return;
      }

      if (response.statusCode == 401) { // Incorrect sentence
        setState(() {
          resultMessage = "❌ Incorrect. Say: \"${sentences[currentSentenceIndex]}\" again.";
        });
        return;
      }

      if (response.statusCode == 200) {
        if (data["training_complete"] == true) {
          setState(() {
            resultMessage = "✅ $message\n🎉 Training Complete!";
            trainingComplete = true;
          });

          await Future.delayed(const Duration(seconds: 3));
          recordVoiceSignature();
        } else {
          setState(() {
            resultMessage = "✅ $message\n🛡️ Deepfake Check: $deepfakeResult";
            currentSentenceIndex++;
          });
        }
      } else {
        setState(() {
          resultMessage = "❌ $message\n🛡️ Deepfake Check: $deepfakeResult";
        });
      }
    } catch (e) {
      setState(() {
        resultMessage = "❌ Error verifying speech: $e";
      });
    }
  }

  Future<void> recordVoiceSignature() async {
  if (!trainingComplete) return;

  setState(() {
    resultMessage = "🎤 Tap the button to start recording your unique voice signature.";
  });

  await Future.delayed(const Duration(seconds: 1)); // Small delay for clarity

  // Ensure the user explicitly starts recording
  String? audioFilePath = await recordAudio(); 

  if (audioFilePath == null) {
    setState(() => resultMessage = "❌ Recording failed.");
    return;
  }

  try {
    var request = http.MultipartRequest(
      "POST", Uri.parse("http://192.168.29.131:5002/create_voice_signature")
    );
    request.fields["username"] = username;
    request.files.add(await http.MultipartFile.fromPath("audio", audioFilePath));

    setState(() {
      resultMessage = "📤 Uploading voice signature...";
    });

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();
    var data = jsonDecode(responseBody);

    if (response.statusCode == 200) {
      setState(() {
        resultMessage = "✅ Voice signature saved successfully!\n🔗 File: ${data['audio_url']}";
      });
    } else {
      setState(() {
        resultMessage = "❌ Failed to save voice signature: ${data['error']}";
      });
    }
  } catch (e) {
    setState(() {
      resultMessage = "❌ Error uploading voice signature: $e";
    });
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Voice Signature Training")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _usernameController,
              decoration: InputDecoration(
                labelText: "Enter Username",
                border: OutlineInputBorder(),
              ),
              onChanged: (value) => username = value,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: fetchSentences,
              child: const Text("📜 Get Sentences"),
            ),
            const SizedBox(height: 20),
            Text(
              sentences.isNotEmpty
                  ? "Say: \"${sentences[currentSentenceIndex]}\""
                  : "Loading sentences...",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: verifySpeech,
              child: Text(isRecording ? "⏳ Recording..." : "🎤 Record & Verify"),
            ),
            if (trainingComplete) ...[
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: recordVoiceSignature,
                child: const Text("🔊 Record Voice Signature"),
              ),
            ],
            const SizedBox(height: 20),
            Text(
              resultMessage,
              style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

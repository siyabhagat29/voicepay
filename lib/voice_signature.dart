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
  List<String> sentences = [];
  int currentSentenceIndex = 0;
  bool isRecording = false;
  String resultMessage = "Waiting for action...";
  final AudioRecorder recorder = AudioRecorder();

  @override
  void initState() {
    super.initState();
    fetchSentences();
  }

  Future<void> fetchSentences() async {
    try {
      var response =
          await http.get(Uri.parse("http://192.168.180.74:5001/get_sentences"));
      if (response.statusCode == 200) {
        var data = jsonDecode(response.body);
        setState(() {
          sentences = List<String>.from(data["sentences"]);
          resultMessage = "📜 Sentences loaded. Tap to start.";
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
  if (sentences.isEmpty) return;

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
        "POST", Uri.parse("http://192.168.180.74:5001/verify_speech"));
    request.files
        .add(await http.MultipartFile.fromPath("audio", audioFilePath));
    request.fields["expected_text"] = sentences[currentSentenceIndex];

    setState(() {
      resultMessage = "📤 Uploading audio...";
    });

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();
    print("Server Response: $responseBody"); // DEBUG PRINT
    var data = jsonDecode(responseBody);

    String deepfakeResult = data["deepfake_result"] ?? "Unknown"; // Get deepfake status
    String message = data["message"] ?? "Unknown response"; // Get message

    setState(() {
      if (response.statusCode == 200) {
        resultMessage = "✅ $message\n🛡️ Deepfake Check: $deepfakeResult";
      } else if (response.statusCode == 403) {
        resultMessage = "🚨 Deepfake detected! Use a real voice.\n🛡️ Deepfake Check: $deepfakeResult";
      } else {
        resultMessage = "❌ $message\n🛡️ Deepfake Check: $deepfakeResult";
      }

      if (currentSentenceIndex < sentences.length - 1) {
        currentSentenceIndex++;
      } else {
        resultMessage = "🎉 Training Completed!";
      }
    });
  } catch (e) {
    setState(() {
      resultMessage = "❌ Error verifying speech: $e";
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
              child:
                  Text(isRecording ? "⏳ Recording..." : "🎤 Record & Verify"),
            ),
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

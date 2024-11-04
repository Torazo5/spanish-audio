import os
import json  # Import json module
import torch
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from TTS.api import TTS
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Determine device (GPU or CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.backends.mps.is_available():
    device = 'mps'
elif torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

# Initialize TTS with a multi-speaker, multi-lingual model
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)
client = OpenAI()

# Importing required classes
from pypdf import PdfReader

# Creating a PDF reader object
pdf_path = './Booklet Ab 11  Unit 1 2024.pdf'  # Replace with your PDF file path
reader = PdfReader(pdf_path)

# Printing the number of pages in the PDF file
print(f'The PDF has {len(reader.pages)} pages.')

curriculum_content = ''
# Iterating through each page to extract and print the text
for page_number in range(len(reader.pages)):
    page = reader.pages[page_number]
    text = page.extract_text()  # Extracting text from the page
    curriculum_content += " " + text

@app.route('/api/chat', methods=['POST'])
def chat_with_gpt():
    data = request.get_json()
    user_prompt = data.get("text", "")
    language = data.get("language", "es")
    speaker_wav = data.get("speaker_wav", 'esp1.wav')

    try:
        # Construct prompt for practice listening exercise using fixed curriculum content
        prompt = f"""
You are a Spanish language teacher preparing a listening practice exercise.

Based on the following curriculum content or topic, please create a listening practice exercise.

Use Spanish for the text and question content, but keep the JSON keys in English.

Format it as a JSON object with the following structure:

{{
  "text": "[The listening text in Spanish]",
  "multiple_choice_questions": [
    {{
      "question": "[Question in Spanish]",
      "options": {{
        "A": "[Option A]",
        "B": "[Option B]",
        "C": "[Option C]",
        "D": "[Option D]"
      }}
    }},
    ...
  ],
  "open_ended_questions": [
    {{
      "question": "[Text in Spanish with blank spaces]"
    }},
    ...
  ],
  "answers": {{
    "multiple_choice": [
      "[Correct option (A, B, C, or D)]",
      ...
    ],
    "open_ended": [
      "[Correct answer in Spanish for blank in Question 1]",
      ...
    ]
  }}
}}

### Curriculum Content or Topic:
"{curriculum_content}"

Please output only the JSON object and ensure it is valid JSON without any additional text.
"""

        # Get GPT-4 response with prompt engineering
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        assistant_message = completion.choices[0].message.content

        # Parse the assistant_message as JSON
        exercise_data = json.loads(assistant_message)

        # Extract the listening text for TTS
        listening_text = exercise_data["text"]
        print('Assistant Message:', assistant_message)
        print('Listening Text:', listening_text)

        # Generate TTS audio with voice cloning if speaker_wav is provided
        audio_path = "output.wav"
        if speaker_wav:
            tts.tts_to_file(text=listening_text, speaker_wav=speaker_wav, language=language, file_path=audio_path)

        # Return both the JSON data and audio file path
        return jsonify({"data": exercise_data, "audio_url": "/api/audio"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An error occurred while processing the request"}), 500

# Serve the audio file
@app.route('/api/audio', methods=['GET'])
def get_audio():
    audio_path = "output.wav"
    return send_file(audio_path, mimetype="audio/wav")

if __name__ == '__main__':
    app.run(debug=True)

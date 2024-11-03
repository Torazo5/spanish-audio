import os
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
    curriculum_content = curriculum_content+ " " + text

@app.route('/api/chat', methods=['POST'])
def chat_with_gpt():
    # Keep user input handling but ignore it
    data = request.get_json()  # This will still receive user input
    user_prompt = data.get("text", "")  # Not used but still kept in the code
    language = data.get("language", "es")
    speaker_wav = data.get("speaker_wav", 'esp1.wav')
    
    try:
        # Construct prompt for practice listening exercise using fixed curriculum content
        prompt = f"""
        You are a Spanish language teacher preparing a listening practice exercise. 

        Based on the following curriculum content or topic, please create a listening practice exercise. Use Spanish for the text and question content, but keep the structure and formatting labels in English, like "**Text**", "**Multiple-Choice Questions**", and "**Answers**". 

        Format it as follows:

        1. **Text**: A short passage in Spanish for the student to listen to.
        2. **Multiple-Choice Questions (MCQs)**: Create between 1 to 3 multiple-choice questions with four answer options (A, B, C, D).
        3. **Open-Ended Questions with Blanks**: Develop between 3 to 5 open-ended questions where some key words are blank for the student to fill in based on their listening.
        4. **Answers**: Provide the correct answers at the bottom for the teacher’s reference.

        ### Curriculum Content or Topic:
        "{curriculum_content}"

        ### Output Format:
        **Text**: [The listening text in Spanish]
        **Multiple-Choice Questions**:
          - MCQ 1: [Question in Spanish with options A, B, C, D]
          - MCQ 2: [Optional question in Spanish with options A, B, C, D]
          - MCQ 3: [Optional question in Spanish with options A, B, C, D]
        **Open-Ended Questions with Blanks**:
          - Question 1: [Text in Spanish with blank spaces]
          - Question 2: [Text in Spanish with blank spaces]
          - Question 3: [Text in Spanish with blank spaces]
        **Answers**:
          - MCQ 1 Answer: [Correct option in Spanish]
          - MCQ 2 Answer: [Correct option in Spanish]
          - MCQ 3 Answer: [Correct option in Spanish]
          - Open-Ended Question 1 Answer: [Correct answer in Spanish for blank in Question 1]
          - Open-Ended Question 2 Answer: [Correct answer in Spanish for blank in Question 2]
          - Open-Ended Question 3 Answer: [Correct answer in Spanish for blank in Question 3]

        Generate this in Spanish with the specified English formatting labels.
        """

        # Get GPT-4 response with prompt engineering
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        assistant_message = completion.choices[0].message.content

        # Extract only the listening text for TTS
        listening_text = extract_listening_text(assistant_message)
        print(assistant_message)
        print('listening text--------------')
        print(listening_text)
        # Generate TTS audio with voice cloning if speaker_wav is provided
        audio_path = "output.wav"
        if speaker_wav:
            tts.tts_to_file(text=listening_text, speaker_wav=speaker_wav, language=language, file_path=audio_path)

        # Return both the text and audio file path
        return jsonify({"text": assistant_message, "audio_url": "/api/audio"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An error occurred while processing the request"}), 500

# Helper function to extract the listening text from the GPT response
def extract_listening_text(response_text):
    # Assuming the listening text is labeled under "- **Text**:"
    start_marker = "**Text**:"
    end_marker = "**Multiple-Choice Questions**:"
    start_index = response_text.find(start_marker) + len(start_marker)
    end_index = response_text.find(end_marker)
    listening_text = response_text[start_index:end_index].strip()
    return listening_text

# Serve the audio file
@app.route('/api/audio', methods=['GET'])
def get_audio():
    audio_path = "output.wav"
    return send_file(audio_path, mimetype="audio/wav")

if __name__ == '__main__':
    app.run(debug=True)

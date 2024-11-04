import os
import json
import torch
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from TTS.api import TTS
from openai import OpenAI  # Adjusted import for OpenAI

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

# Initialize OpenAI client
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
def summarize_curriculum(curriculum_content):
    summarize_prompt = f"""
    You are an assistant that summarizes educational curriculum content.

    Please summarize the following curriculum content into an extensive list of key topics, each accompanied by a brief example.
    There is no need to create number lists or bold words, just information. 
    ### Curriculum Content:
    {curriculum_content}

    ### Summary:
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI."},
                {"role": "user", "content": summarize_prompt}
            ],
            max_tokens=1000  # Adjust based on the desired summary length
        )
        summary = completion.choices[0].message.content
        return summary
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

curriculum = summarize_curriculum(curriculum_content)
print(curriculum)

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

Ensure that:
- There are between 3 and 5 multiple-choice questions.
- There are between 4 and 5 open-ended questions.
- All questions are directly related to the listening text and do not ask personal or unrelated questions.

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
"{curriculum}"

Please output only the JSON object and ensure it is valid JSON without any additional text.
"""

        # Get GPT-4 response with prompt engineering
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
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

# New endpoint to handle submitted answers
@app.route('/api/submit_answers', methods=['POST'])
def submit_answers():
    data = request.get_json()
    exercise_data = data.get('exercise_data')
    user_answers = data.get('user_answers')

    try:
        listening_text = exercise_data['text']
        feedback = {'mcq_feedback': [], 'open_ended_feedback': []}

        print("Received exercise data:", exercise_data)  # Debug log
        print("Received user answers:", user_answers)  # Debug log

        # Evaluate Multiple-Choice Questions
        mcq_questions = exercise_data.get('multiple_choice_questions', [])
        mcq_correct_answers = exercise_data.get('answers', {}).get('multiple_choice', [])
        user_mcq_answers = user_answers.get('mcq_answers', [])

        print("MCQ questions:", mcq_questions)  # Debug log
        print("Correct MCQ answers:", mcq_correct_answers)  # Debug log
        print("User MCQ answers:", user_mcq_answers)  # Debug log

        for idx, (question_data, user_answer) in enumerate(zip(mcq_questions, user_mcq_answers)):
            question = question_data['question']
            options = question_data['options']
            print(f"Processing MCQ {idx + 1}:")  # Debug log
            print("Question:", question)  # Debug log
            print("Options:", options)  # Debug log
            print("User selected option:", user_answer)  # Debug log

            # Prepare the prompt for GPT-4
            prompt = f"""
You are an assistant that evaluates answers to listening comprehension questions.

Given the following listening text in Spanish:

"{listening_text}"

And the following multiple-choice question:

Question: "{question}"
Options:
A: {options['A']}
B: {options['B']}
C: {options['C']}
D: {options['D']}

The user selected option: "{user_answer}"

Determine if the user's answer is correct based solely on the listening text and question. Respond with "Correct" or "Incorrect" and provide a brief explanation in English.
"""

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            evaluation = completion.choices[0].message.content.strip()
            print("GPT-4 evaluation response:", evaluation)  # Debug log
            feedback['mcq_feedback'].append({
                'question_index': idx,
                'evaluation': evaluation
            })

        # Evaluate Open-Ended Questions
        open_ended_questions = exercise_data.get('open_ended_questions', [])
        user_open_ended_answers = user_answers.get('open_ended_answers', [])

        print("Open-ended questions:", open_ended_questions)  # Debug log
        print("User open-ended answers:", user_open_ended_answers)  # Debug log

        for idx, (question_data, user_answer) in enumerate(zip(open_ended_questions, user_open_ended_answers)):
            question = question_data['question']
            print(f"Processing Open-ended Question {idx + 1}:")  # Debug log
            print("Question:", question)  # Debug log
            print("User answer:", user_answer)  # Debug log

            # Prepare the prompt for GPT-4
            prompt = f"""
You are an assistant that evaluates answers to listening comprehension questions.

Given the following listening text in Spanish:

"{listening_text}"

And the following open-ended question:

Question: "{question}"

The user's answer: "{user_answer}"

Determine if the user's answer is correct based solely on the listening text and question. Respond with "Correct" or "Incorrect" and provide a brief explanation in English.
"""

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            evaluation = completion.choices[0].message.content.strip()
            print("GPT-4 evaluation response:", evaluation)  # Debug log
            feedback['open_ended_feedback'].append({
                'question_index': idx,
                'evaluation': evaluation
            })

        # Return the feedback to the frontend
        print("Feedback to return:", feedback)  # Debug log
        return jsonify({'feedback': feedback})

    except Exception as e:
        print("Error during answer evaluation:", e)  # Detailed error log
        return jsonify({"error": "An error occurred while evaluating the answers"}), 500

if __name__ == '__main__':
    app.run(debug=True)

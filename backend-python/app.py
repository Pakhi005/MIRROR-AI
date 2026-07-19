import os
import json
import tempfile
from flask import Flask, jsonify, request
from flask_cors import CORS
from interviewer import conduct_interview_graph, transcribe_audio
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Python Backend!"})

@app.route('/start-interview', methods=['POST'])
def start_interview():
    data = request.json
    jd_text = data.get('jd')
    email = data.get('email', '')
    if not jd_text:
        return jsonify({"error": "No Job Description provided"}), 400
    
    result = conduct_interview_graph(jd_text, "", 1, [], email)
    return jsonify(result)

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    # Frontend now sends multipart/form-data
    jd_text = request.form.get('jd')
    email = request.form.get('email', '')
    q_num = request.form.get('question_number')
    
    try:
        history = json.loads(request.form.get('history', '[]'))
    except json.JSONDecodeError:
        history = []
        
    audio_file = request.files.get('audio')
    
    if not all([jd_text, q_num]):
        return jsonify({"error": "Missing required fields"}), 400
        
    answer_text = ""
    if audio_file:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
            
        answer_text = transcribe_audio(temp_path)
        os.remove(temp_path)
    else:
        answer_text = request.form.get('answer', '(No audio provided)')
        
    result = conduct_interview_graph(jd_text, answer_text, int(q_num), history, email)
    
    # Return transcript along with the evaluation
    result['transcript'] = answer_text
    
    return jsonify(result)

@app.route('/end-interview', methods=['POST'])
def end_interview():
    # Could be multipart/form-data if they hit 'Stop' and we immediately ended
    # The frontend code we wrote actually uses FormData for end-interview as well
    jd_text = request.form.get('jd')
    if jd_text is None:
        # Fallback to JSON in case it was called differently
        if request.is_json:
            jd_text = request.json.get('jd')
            email = request.json.get('email', '')
            history = request.json.get('history', [])
        else:
            return jsonify({"error": "Missing required fields"}), 400
    else:
        email = request.form.get('email', '')
        try:
            history = json.loads(request.form.get('history', '[]'))
        except json.JSONDecodeError:
            history = []
    
    # For end interview we don't have a new answer typically, 
    # but we will just pass empty string as we evaluate the whole history.
    result = conduct_interview_graph(jd_text, "", 13, history, email)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000, debug=True)

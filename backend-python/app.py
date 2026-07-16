from flask import Flask, jsonify, request
from flask_cors import CORS
from interviewer import conduct_interview
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
    if not jd_text:
        return jsonify({"error": "No Job Description provided"}), 400
    
    result = conduct_interview(jd_text, "", 1, [])
    return jsonify(result)

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    data = request.json
    jd_text = data.get('jd')
    answer = data.get('answer')
    q_num = data.get('question_number')
    history = data.get('history', [])
    
    if not all([jd_text, answer, q_num]):
        return jsonify({"error": "Missing required fields"}), 400
        
    result = conduct_interview(jd_text, answer, q_num, history)
    return jsonify(result)

@app.route('/end-interview', methods=['POST'])
def end_interview():
    data = request.json
    jd_text = data.get('jd')
    answer = data.get('answer')
    history = data.get('history', [])
    
    result = conduct_interview(jd_text, answer, 6, history)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000, debug=True)


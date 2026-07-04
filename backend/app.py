from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import pdfplumber
from groq import Groq

load_dotenv()

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_ai(prompt):
    response = client.chat.completions.create(
       model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

@app.route('/')
def home():
    return {"message": "PrepMate-AI Backend Running! ✅"}

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    from pymongo import MongoClient
    import bcrypt
    mongo = MongoClient(os.getenv("MONGO_URI"))
    db = mongo['prepmate']
    users = db['users']
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if users.find_one({'email': email}):
        return jsonify({'error': 'Email already exists!'}), 400
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({'name': name, 'email': email, 'password': hashed})
    return jsonify({'message': 'Registered successfully!'})

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    from pymongo import MongoClient
    import bcrypt
    import jwt
    import datetime
    mongo = MongoClient(os.getenv("MONGO_URI"))
    db = mongo['prepmate']
    users = db['users']
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = users.find_one({'email': email})
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid credentials!'}), 401
    token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, os.getenv("JWT_SECRET"), algorithm='HS256')
    return jsonify({'token': token, 'user': {'name': user['name'], 'email': user['email']}})

@app.route('/analyze-resume', methods=['POST', 'OPTIONS'])
def analyze_resume():
    if request.method == 'OPTIONS':
        return '', 200
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400
    file = request.files['resume']
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    if not text:
        return jsonify({"error": "PDF lo text ledu!"}), 400
    prompt = f"""
    Analyze this resume and provide:
    1. Overall Score (out of 100)
    2. Strengths (3 points)
    3. Weaknesses (3 points)
    4. Improvements (3 points)
    Resume: {text}
    """
    try:
        result = ask_ai(prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/company-questions', methods=['POST', 'OPTIONS'])
def company_questions():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    company = data.get('company')
    role = data.get('role')
    difficulty = data.get('difficulty')
    prompt = f"Generate 10 {difficulty} level interview questions for {role} position at {company}. Include both technical and behavioral questions. Format as numbered list."
    try:
        result = ask_ai(prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mock-questions', methods=['POST', 'OPTIONS'])
def mock_questions():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    role = data.get('role')
    experience = data.get('experience')
    prompt = f'Generate 5 interview questions for {role} with {experience} experience. Return ONLY a JSON array like: ["Q1", "Q2", "Q3", "Q4", "Q5"]'
    try:
        result = ask_ai(prompt)
        import json
        text = result.strip().replace('```json', '').replace('```', '')
        questions = json.loads(text)
        return jsonify({"questions": questions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mock-feedback', methods=['POST', 'OPTIONS'])
def mock_feedback():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    prompt = f"Interview Question: {question}\nCandidate Answer: {answer}\nProvide brief feedback in 3-4 lines."
    try:
        result = ask_ai(prompt)
        return jsonify({"feedback": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dsa-problem', methods=['POST', 'OPTIONS'])
def dsa_problem():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    topic = data.get('topic')
    difficulty = data.get('difficulty')
    prompt = f"Generate one {difficulty} level DSA problem on {topic}. Include problem statement and example input/output."
    try:
        result = ask_ai(prompt)
        return jsonify({"problem": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dsa-feedback', methods=['POST', 'OPTIONS'])
def dsa_feedback():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    problem = data.get('problem')
    code = data.get('code')
    prompt = f"DSA Problem: {problem}\nStudent Code: {code}\nReview this solution and provide feedback on correctness, time complexity, and improvements."
    try:
        result = ask_ai(prompt)
        return jsonify({"feedback": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/profile', methods=['GET', 'OPTIONS'])
def get_profile():
    if request.method == 'OPTIONS':
        return '', 200
    from pymongo import MongoClient
    import jwt
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
        email = decoded['email']
    except Exception:
        return jsonify({'error': 'Invalid or expired token'}), 401

    mongo = MongoClient(os.getenv("MONGO_URI"))
    db = mongo['prepmate']
    users = db['users']
    user = users.find_one({'email': email})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'name': user.get('name', ''),
        'email': user.get('email', ''),
        'targetRole': user.get('targetRole', ''),
        'experience': user.get('experience', '')
    })

@app.route('/profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS':
        return '', 200
    from pymongo import MongoClient
    import jwt
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
        email = decoded['email']
    except Exception:
        return jsonify({'error': 'Invalid or expired token'}), 401

    data = request.json
    name = data.get('name')
    targetRole = data.get('targetRole')
    experience = data.get('experience')

    mongo = MongoClient(os.getenv("MONGO_URI"))
    db = mongo['prepmate']
    users = db['users']
    users.update_one(
        {'email': email},
        {'$set': {'name': name, 'targetRole': targetRole, 'experience': experience}}
    )
    return jsonify({'message': 'Profile updated successfully!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

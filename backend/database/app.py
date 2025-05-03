from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import hashlib
import os
from bson import ObjectId
import random
import string

# -------------------- Initialize Flask App --------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# -------------------- Connect to MongoDB --------------------
try:
    client = MongoClient("mongodb+srv://b23152:1997january@cluster0.cj44rwl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise e

db = client["troubleshooter"]
user_collection = db["user"]
global_collection = db["qna"]
user_credentials_collection = db["user_credentials"]

# -------------------- Dummy Answer Generator --------------------
def generate_answer(question):
    return f"This is a dummy answer for: {question}"

# -------------------- Routes --------------------
from bson.objectid import ObjectId

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    user_id = data.get("user_id")
    question = data.get("question")
    ques_id = data.get("ques_id")

    if not user_id or not question or not ques_id:
        return jsonify({"error": "Missing user_id, question, or ques_id"}), 400

    answer = generate_answer(question)

    chat_entry = {
        "ques_id": ques_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    }

    user_collection.update_one(
        {"user_id": user_id},
        {"$push": {"chat_history": chat_entry}},
        upsert=True
    )

    qna_doc = {
        "ques_id": ques_id,
        "question": question,
        "answer": answer
    }
    global_collection.insert_one(qna_doc)

    return jsonify({
        "answer": answer,
        "ques_id": ques_id
    })

@app.route("/history/<user_id>", methods=["GET"])
def get_user_history(user_id):
    history = list(user_collection.find({"user_id": user_id}, {"_id": 0}))
    return jsonify(history)

@app.route("/qna/<ques_id>", methods=["GET"])
def get_answer_by_ques_id(ques_id):
    result = global_collection.find_one({"ques_id": ques_id}, {"_id": 0})
    if not result:
        return jsonify({"error": "Question ID not found"}), 404
    return jsonify(result)

@app.route("/user/questions/<user_id>", methods=["GET"])
def get_user_questions(user_id):
    user_doc = user_collection.find_one({"user_id": user_id}, {"_id": 0, "chat_history.question": 1})
    
    if not user_doc or "chat_history" not in user_doc:
        return jsonify({"error": "No history found for this user"}), 404

    questions = [entry["question"] for entry in user_doc["chat_history"] if "question" in entry]
    return jsonify({"user_id": user_id, "questions": questions})

@app.route("/auth", methods=["POST"])
def authenticate_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = user_credentials_collection.find_one({"username": username, "password": password})
    if user:
        return jsonify({"status": "success", "user_id": user["user_id"]})
    return jsonify({"status": "failure", "message": "Invalid credentials"}), 401

@app.route("/signup", methods=["POST"])
def signup_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "failure", "message": "Username and password required"}), 400

    # Check if username already exists
    existing_user = user_credentials_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"status": "failure", "message": "Username already exists"}), 409

    # Create new user with a unique user_id
    user_id = hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

    user_credentials_collection.insert_one({
        "username": username,
        "password": password,
        "user_id": user_id
    })

    return jsonify({"status": "success", "user_id": user_id})



# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# route to get answer using question object id 
@app.route('/get-answer', methods=['GET'])
def get_answer_by_object_id():
    object_id = request.args.get("objectId")
    if not object_id:
        return jsonify({"error": "Missing objectId"}), 400

    result = global_collection.find_one({"_id": ObjectId(object_id)}, {"_id": 0})
    if not result:
        return jsonify({"error": "Object ID not found"}), 404

    return jsonify(result)


# endpoint to add question and answer to the database
def generate_ques_id(length=24):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@app.route('/add-qna', methods=['POST'])
def add_qna():
    # Get the input data (question and answer)
    data = request.json
    question = data.get('question')
    answer = data.get('answer')

    if not question or not answer:
        return jsonify({"error": "Missing question or answer"}), 400

    # Generate random ques_id
    ques_id = generate_ques_id()

    # Insert the new Q&A entry into the database
    new_qna = {
        "question": question,
        "answer": answer,
        "ques_id": ques_id
    }

    result = global_collection.insert_one(new_qna)

    # Return the ObjectId of the newly created document
    return jsonify({"objectId": str(result.inserted_id), "ques_id": ques_id}), 201









# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)

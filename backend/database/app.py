from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

# -------------------- Load Environment Variables --------------------

# -------------------- Initialize Flask App --------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# -------------------- Connect to MongoDB --------------------

try:
    client=MongoClient("mongodb+srv://b23152:1997january@cluster0.cj44rwl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise e

db = client["troubleshooter"]
user_collection = db["user"]
global_collection = db["qna"]
user_credentials_collection=db["user_credentials"]


# -------------------- Dummy Answer Generator --------------------
def generate_answer(question):
    # Replace this with your actual RAG pipeline later
    return f"This is a dummy answer for: {question}"

# -------------------- Routes --------------------

# Route to handle question asking and storing in DB
from bson.objectid import ObjectId  # Import at the top if not already

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    user_id = data.get("user_id")
    question = data.get("question")
    ques_id = data.get("ques_id")  # <-- You provide this in the request

    if not user_id or not question or not ques_id:
        return jsonify({"error": "Missing user_id, question, or ques_id"}), 400

    answer = generate_answer(question)

    chat_entry = {
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    }

    # Store in user chat history
    user_collection.update_one(
        {"user_id": user_id},
        {"$push": {"chat_history": chat_entry}},
        upsert=True
    )

    # Store in qna collection with custom ques_id
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



# Route to get user's chat history
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

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)

import os
from typing import List
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import requests
import pickle

load_dotenv()

embedder = HuggingFaceEmbeddings(
    model_name="intfloat/e5-base-v2",
    model_kwargs={"device": "cpu"}  # Set to "cuda" if using GPU
)

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.7,
    max_length=200
)


relevance_prompt_template = ChatPromptTemplate.from_messages([
    ("system", 
     "You have been given some  questions and you are responsible for determining whether these given set of questions is helpful in answering a user's query.\n\n"
     "**Rules for Answering:**\n"
     "- Read the user query and the given list of questions.\n"
     "- If the given questions are closely related to the query and could help address it and it is related to MATLAB troubleshooting, respond with single word **'yes'**.\n"
     "- Else respond with single word **'no'**.\n"
     "- If unsure, respond with single word **'no'**.\n\n"
     "**Response Format:**\n"
     "- Reply with exactly one word: **yes** or **no** (lowercase).\n"
     "- No punctuation, no explanations, no formatting—only a single word response."
     "- Do not provide any extra questions from your side or add any other text or explanation.\n"
    ),
    ("user", "User Query: {query}\n\n Questions:\n{retrieved_questions}")
])



VECTOR_DB_PATH = "./qnaDB"

# qnaDB 
def AddQuestionQnaDb(question: str, object_id: str):
    doc = Document(
        page_content=question,
        metadata={"objectId": object_id}
    )

    if os.path.exists(os.path.join(VECTOR_DB_PATH, "index.faiss")):
        db = FAISS.load_local(VECTOR_DB_PATH, embedder, allow_dangerous_deserialization=True)
        db.add_documents([doc])
    else:
        db = FAISS.from_documents([doc], embedder)

    db.save_local(VECTOR_DB_PATH)
    print(f"✅ Added question to qnaDB with ObjectID: {object_id}")


# qnaDB 
def QuestionFinderAgent(query: str, k: int = 1):
    if not os.path.exists(os.path.join(VECTOR_DB_PATH, "index.faiss")):
        print("❌ qnaDB does not exist yet.")
        return "no"

    db = FAISS.load_local(VECTOR_DB_PATH, embedder, allow_dangerous_deserialization=True)
    results = db.similarity_search(query, k=k)

    if not results:
        return "no"

    formatted_results = [
        {
            "question": doc.page_content,
            "objectId": doc.metadata.get("objectId")
        }
        for doc in results
    ]
    print(f"🤖 Retrieved {len(formatted_results)} questions from qnaDB.")

    questions_text = "\n".join([f"- {item['question']}" for item in formatted_results])
    print(f"🤖 Retrieved Questions:\n{questions_text}")

    prompt = relevance_prompt_template.format_messages(
        query=query,
        retrieved_questions=questions_text
    )
    llm_response = llm.invoke(prompt).strip().lower()
    print(f"🤖 LLM Response: {llm_response}")

    if "yes" in llm_response:
        return formatted_results
    else:
        return "no"




# main database
def add_qna_to_backend(question: str, answer: str):
    url = "http://127.0.0.1:5000/add-qna" 
    data = {
        "question": question,
        "answer": answer
    }
    response = requests.post(url, json=data)
    if response.status_code == 201:
        result = response.json()
        object_id = result["objectId"]
        AddQuestionQnaDb(question, object_id)
        print(f"✅ Successfully added Q&A to backend with ObjectID: {object_id}")
        return object_id  
    else:
        print("Failed to add Q&A to backend.")
        return None




if __name__ == "__main__":
    # AddQuestionQnaDb("How do I fix a segmentation fault in MATLAB?", "661fc8d213c9b34567bcde12")
    # AddQuestionQnaDb("What is the use of Simulink in MATLAB?", "661fc8d213c9b34567bcde13")

    # query = "How to resolve MATLAB system error?"
    # output = QuestionFinderAgent(query, k=4)

    # if output == "no":
    #     print("🤖 Query not relevant.")
    # else:
    #     print("🤖 Top Similar Questions:")
    #     for i, match in enumerate(output, 1):
    #         print(f"\nMatch {i}:")
    #         print(f"Question: {match['question']}")
    #         print(f"Mongo ObjectID: {match['objectId']}")

    question = "What is a segmentation fault?"
    answer = "A segmentation fault is caused by accessing memory that the CPU cannot read or write."
    object_id = add_qna_to_backend(question, answer)
    if object_id:
        print(f"✅ Successfully added question with ObjectID: {object_id}")
    else:
        print("Failed to add the question.")

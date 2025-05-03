import re
from langchain.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
import requests


BACKEND_URL = "http://127.0.0.1:5000/get-answer"
def fetch_answer(object_id):
    try:
        response = requests.get(f"{BACKEND_URL}?objectId={object_id}")
        if response.status_code == 200:
            return response.json().get("answer", "")
        else:
            return ""
    except Exception as e:
        print(f"Error fetching answer for {object_id}: {e}")
        return ""



llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.3,
    max_length=512
)

rag_prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert assistant. Your task is to answer the user's query using the provided list of related question-answer pairs.\n\n"
     "**Instructions:**\n"
     "- Read the user's query carefully.\n"
     "- Use the provided Q&A pairs as knowledge base.\n"
     "- Provide the answer of user query strictly on the Q&A pairs.\n"
     "**Response Format:**\n"
     "- Reply with single answer of query. No extra explanation needed.\n"
    ),
    ("user", 
     "User Query: {query}\n\n"
     "Related Question-Answer Pairs:\n{qa_pairs}")
])


def extract_final_answer(llm_response: str) -> str:
    last_a_index = llm_response.rfind("A:")
    if last_a_index != -1:
        return llm_response[last_a_index + 2:].strip()
    return llm_response[last_a_index + 2:].strip()


def AnswerQnaAgent(query: str, related_qa) -> str:
    qa_pairs = []
    for item in related_qa:
        answer = fetch_answer(item["objectId"]) # database backend call
        if answer:
            qa_pairs.append({
                "question": item["question"],
                "answer": answer
            })
    formatted_qa = "\n\n".join(
        f"Q: {pair['question']}\nA: {pair['answer']}" for pair in qa_pairs
    )
    for pair in qa_pairs:
        print(f"Q: {pair['question']}\nA: {pair['answer']}")
    prompt = rag_prompt_template.format_messages(query=query, qa_pairs=formatted_qa)
    response = llm.invoke(prompt).strip()
    final_answer = extract_final_answer(response)
    return final_answer




if __name__ == "__main__":

    query = "How do I fix segmentation faults in MATLAB?"
    # related_qa = [
    #     {"question": "What causes segmentation faults in MATLAB?", "answer": "Segmentation faults usually occur due to invalid memory access in compiled MEX functions."},
    #     {"question": "How to debug segmentation faults?", "answer": "Use MATLAB's crash dump logs and debug with GDB if MEX is involved."},
    #     {"question": "Can Simulink models cause segmentation faults?", "answer": "Yes, if S-functions have invalid memory access or indexing issues."}
    # ]
    related_qa = [
        {"question": "How to debug segmentation faults?", "objectId": "68160d8d5cd131e138ad33cd"},
        {"question": "What causes segmentation faults in MATLAB?", "objectId": "68160d1d5cd131e138ad33cc"},
        {"question": "Can Simulink models cause segmentation faults?", "objectId": "68160dbb5cd131e138ad33ce"},
    ]

    answer = AnswerQnaAgent(query, related_qa)
    print("📌 Answer:\n", answer)

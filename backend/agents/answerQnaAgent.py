import re
from langchain.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint

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
    formatted_qa = "\n\n".join(
        f"Q: {pair['question']}\nA: {pair['answer']}" for pair in related_qa
    )
    prompt = rag_prompt_template.format_messages(query=query, qa_pairs=formatted_qa)
    response = llm.invoke(prompt).strip()
    final_answer = extract_final_answer(response)
    return final_answer




if __name__ == "__main__":

    query = "How do I fix segmentation faults in MATLAB?"
    related_qa = [
        {"question": "What causes segmentation faults in MATLAB?", "answer": "Segmentation faults usually occur due to invalid memory access in compiled MEX functions."},
        {"question": "How to debug segmentation faults?", "answer": "Use MATLAB's crash dump logs and debug with GDB if MEX is involved."},
        {"question": "Can Simulink models cause segmentation faults?", "answer": "Yes, if S-functions have invalid memory access or indexing issues."}
    ]

    answer = AnswerQnaAgent(query, related_qa)
    print("📌 Answer:\n", answer)

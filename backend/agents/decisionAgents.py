import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain.prompts.chat import ChatPromptTemplate

load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

embedder = HuggingFaceEmbeddings(
    model_name="intfloat/e5-base-v2",
    model_kwargs={"device": "cpu"}
)

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.7,
    max_length=200
)

relevance_prompt_template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an AI assistant responsible for determining whether a user's query requires retrieving documents related to troubleshooting MATLAB issues.\n\n"
     "**Rules for Answering:**\n"
     "- If the query contains greetings or casual conversation (e.g., 'Hi', 'Hello', 'How are you?', 'Good morning'), respond with **'no'**.\n"
     "- If the query is vague, general, or not clearly asking about MATLAB errors, configuration issues, installation problems, toolboxes, firewalls, performance issues, or crashes, respond with **'no'**.\n"
     "- Only respond **'yes'** if the query specifically involves technical problems, errors, warnings, software bugs, or diagnostic issues *in MATLAB*.\n"
     "- If unsure, respond with **'no'**.\n\n"
     "**Response Format:**\n"
     "- Reply with exactly one word: **yes** or **no** (lowercase).\n"
     "- No punctuation, no explanations, no formatting—only a single word response."
    ),
    ("user", "User Query: {query}")
])

def isQueryRelevantAgent(query: str) -> str:
    try:
        formatted_prompt = relevance_prompt_template.format_messages(query=query)
        response = llm.invoke(formatted_prompt).strip().lower()

        if "yes" in response:
            return "yes"
        elif "no" in response:
            return "no"
        else:
            return "no"
    except Exception as e:
        return f"❌ Error: {str(e)}"





# Entry point
if __name__ == "__main__":
    query = "how are you doing?"
    relevance = isQueryRelevantAgent(query)
    print("📌 Query Relevant:", relevance)

    if relevance == "yes":
        print("🤖", "yes")
    else:
        print("🤖 This query is not related to MATLAB troubleshooting.")

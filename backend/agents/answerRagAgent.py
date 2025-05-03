import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)



# llm =  HuggingFaceEndpoint(
#     repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", 
#     temperature=0.7,
#     max_length=200)
genai.configure(api_key=api_key)
llm = genai.GenerativeModel("gemini-2.0-flash")


prompt_template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an expert assistant helping engineers troubleshoot and optimize MATLAB systems.\n\n"
     "**Instructions:**\n"
     "- Use only the given context to answer the question.\n"
     "- Do not make up information or rely on prior knowledge.\n"
     "- If the context is insufficient, respond strictly with: \"I don't know\".\n"
     "- Be concise, clear, and technical in your answer.\n\n"
     "**Response Format Example:**\n"
     "1. **Summary:** A short, direct answer to the user's query.\n"
     "2. **Cause (if applicable):** Explain what may be causing the issue.\n"
     "3. **Resolution:** Steps or methods to resolve the issue.\n"
     "4. **Best Practices / Notes (optional):** Extra advice or caution if necessary."
    ),
    ("user", 
     "Context:\n{context}\n\n"
     "Question:\n{question}\n\n"
     "Answer:"
    )
])

def AnswerRagAgent(query: str, vectorstore_name: str, k: int = 6):
    try:
        index_path = f"/home/piyush/DCIM/code/projects/DL/DLHackathon/backend/{vectorstore_name}"
        # index_path = vectorstore_name
        vectorstore = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)


        docs = vectorstore.similarity_search(query, k=k)
        print(f"🔍 Found {len(docs)} relevant documents.")
        # for i, doc in enumerate(docs):
        #     print(f"\nDocument {i + 1}:")
        #     print(f"Content: {doc.page_content}")
        #     print(f"Metadata: {doc.metadata}\n")
        context = "\n\n".join([doc.page_content for doc in docs])
        # prompt = prompt_template.format(context=context, question=query)
        # response = llm.invoke(prompt)
        formatted_messages = prompt_template.format_messages(context=context, question=query)
        prompt_str = "\n\n".join([f"{msg.content}" for msg in formatted_messages])
        response = llm.generate_content(prompt_str)
        llm_response = response.text.strip().lower()
        # return response.strip()
        return llm_response

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    # query = "How do I fix segmentation faults in MATLAB?"
    # query = "How to resolve MATLAB system error?"
    query = "Where is the Real-Time tab?"
    # query = "How to resolve MATLAB segmentation fault?"
    # query = "when Simulink models cause seg faults?"
    # query = "What is ldd:FATAL: Could not load library xyz.so? How do I fix it?"
    vectorstore_name = "faiss_vector_store"
    answer = AnswerRagAgent(query, vectorstore_name)
    print("🤖", answer)

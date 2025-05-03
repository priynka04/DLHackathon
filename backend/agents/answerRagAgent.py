import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)


# llm = HuggingFaceEndpoint(
#     repo_id="mistralai/Mistral-7B-Instruct-v0.1",
#     task="text-generation",
#     temperature=0.7,
#     max_new_tokens=512,
# )
llm =  HuggingFaceEndpoint(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",  # ✅ Correct model
    temperature=0.7,
    max_length=200
    )

# 3. Prompt template
prompt_template = PromptTemplate.from_template("""
You are an expert assistant helping engineers troubleshoot and optimize MATLAB systems.
Use only the given context to answer the question. Do not make up anything.
Only answer the question based on the context provided.
If the context does not contain enough information to answer the question, say "I don't know".

Context:
{context}

Question:
{question}

Answer:
""")

def AnswerRagAgent(query: str, vectorstore_name: str, k: int = 6):
    try:
        index_path = f"backend/MainVS/{vectorstore_name}"
        vectorstore = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)


        docs = vectorstore.similarity_search(query, k=k)
        print(f"🔍 Found {len(docs)} relevant documents.")
        for i, doc in enumerate(docs):
            print(f"\nDocument {i + 1}:")
            print(f"Content: {doc.page_content}")
            print(f"Metadata: {doc.metadata}\n")
        context = "\n\n".join([doc.page_content for doc in docs])

        # prompt = prompt_template.format(context=context, question=query)

        # response = llm.invoke(prompt)
        # return response.strip()
        return "s"

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    query = "What is ldd:FATAL: Could not load library xyz.so? How do I fix it?"
    vectorstore_name = "faiss_troubleshooting_system_configuration"
    answer = AnswerRagAgent(query, vectorstore_name)
    print("🤖", answer)

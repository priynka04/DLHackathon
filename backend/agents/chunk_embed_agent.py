# agents/chunk_embed_agent.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

import requests
from bs4 import BeautifulSoup


def scrape_matlab_page(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    content = soup.get_text(separator='\n')
    return content.strip()



# Load embedding model
embed_model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def chunk_text(text, chunk_size=500, overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    return splitter.split_text(text)

def embed_and_store(chunks, metadata, collection_name="matlab_docs"):
    # embed_model = embedding_functions.SentenceTransformerEmbeddingFunction(
    #     model_name="all-MiniLM-L6-v2"
    # )

    client = PersistentClient(path="./vectorstore")

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_model
    )

    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[metadata],
            ids=[f"doc_{i}"]
        )

    print("✅ Vectorstore saved successfully.")


def query_vectorstore(query, collection_name="matlab_docs"):
    # Step 1: Connect to ChromaDB
    client = PersistentClient(path="./vectorstore")
    collection = client.get_collection(name=collection_name)

    # Step 2: Convert query to embedding
    query_embedding = embed_model([query])  # Embeds the query

    # Step 3: Perform similarity search
    results = collection.query(
        query_embeddings=query_embedding,  # Pass the embedded query
        n_results=5
    )

    return results
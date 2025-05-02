# main.py
from agents.chunk_embed_agent import chunk_text, embed_and_store,query_vectorstore, scrape_matlab_page

# # 1. Define a URL
# url = "https://in.mathworks.com/help/slrealtime/ug/troubleshoot-communication-failure-through-firewall.html"
# text = scrape_matlab_page(url)

# # 2. Chunk
# chunks = chunk_text(text)

# # 3. Add Metadata
# metadata = {
#     "source": url,
#     "title": "MATLAB Troubleshooting"
# }

# # 4. Embed and Store
# embed_and_store(chunks, metadata)

# print("✅ Embedding and storage complete.")


# 5. Query the Vectorstore
query = "What is the troubleshooting process for communication failure through firewall?"
results = query_vectorstore(query)
print("\n📌 Top Matching Chunks:\n")
for i, doc in enumerate(results['documents'][0]):
    print(f"--- Result {i+1} ---")
    print(doc)
    print()
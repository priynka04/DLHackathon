import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

BASE_URL = "https://in.mathworks.com"
START_PATH = "/help/slrealtime/ug/troubleshooting-basics.html"
MAX_PAGES = None  # or set to limit pages for testing

visited = set()
pages_to_visit = []
all_texts = []  # will hold tuples (url, markdown_content)

# Initialize embedder and header-based splitter
embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)
# Split on H2 and H3 to retain heading context; overlap small to preserve continuity
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "H2"), ("###", "H3")],
    strip_headers=False,
)

# Crawler functions
def fetch_soup(url: str) -> BeautifulSoup:
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logging.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_page_markdown(url: str) -> str:
    """
    Fetches the main content sections and converts to Markdown,
    preserving header hierarchy for splitter context.
    """
    soup = fetch_soup(url)
    if not soup:
        return ""

    content_secs = soup.find_all("section", {"itemprop": "content"})
    md_lines = []

    def walk(node):
        if not isinstance(node, Tag):
            return
        # Headers to markdown
        if node.name in ("h2", "h3", "h4"):
            level = int(node.name[1])
            text = node.get_text(" ", strip=True)
            md_lines.append(f"{'#'*level} {text}")
        elif node.name == "p":
            md_lines.append(node.get_text(" ", strip=True))
        elif node.name == "li":
            md_lines.append(f"- {node.get_text(' ', strip=True)}")
        elif node.name == "pre":
            md_lines.append("```\n" + node.get_text(strip=True) + "\n```")
        # recurse
        for child in node.children:
            walk(child)

    for sec in content_secs:
        walk(sec)

    return "\n\n".join(md_lines)


def find_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        parsed = urlparse(full)
        if parsed.netloc.endswith("mathworks.com") and "/help/slrealtime/ug/" in parsed.path:
            clean = parsed.scheme + "://" + parsed.netloc + parsed.path
            if clean not in visited:
                links.append(clean)
    return links

# Begin crawl
start_url = urljoin(BASE_URL, START_PATH)
pages_to_visit.append(start_url)

while pages_to_visit and (MAX_PAGES is None or len(visited) < MAX_PAGES):
    url = pages_to_visit.pop(0)
    if url in visited:
        continue
    logging.info(f"Visiting: {url}")
    visited.add(url)

    soup = fetch_soup(url)
    if not soup:
        continue

    md = extract_page_markdown(url)
    if md:
        all_texts.append((url, md))

    for link in find_links(soup, url):
        pages_to_visit.append(link)

logging.info(f"Crawled {len(visited)} pages.")
# Persist visited URLs
with open("visited.txt", "w") as vf:
    for link in visited:
        vf.write(link + "\n")
logging.info("Saved visited URLs to visited.txt")

# Chunk, embed, and store metadata including heading context
from langchain.schema import Document
chunks = []
for url, md in all_texts:
    docs = splitter.split_text(md)
    for doc in docs:
        # Each doc has .page_content and metadata {'header': '## ...'}
        heading = doc.metadata.get('header', 'Unknown')
        chunks.append(Document(
            page_content=doc.page_content,
            metadata={"source": url, "heading": heading}
        ))

logging.info(f"Prepared {len(chunks)} chunks with heading metadata.")

# Build single FAISS store from Document objects
db = FAISS.from_documents(chunks, embedder)

# Persist the unified vector store
out_dir = "backend/faiss_vector_store"
db.save_local(out_dir)
logging.info(f"Saved FAISS vector store with heading metadata to {out_dir}")

print("Done building vector store with heading context!")

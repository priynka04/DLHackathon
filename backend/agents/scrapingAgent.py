import requests                                        # HTTP requests :contentReference[oaicite:0]{index=0}
from bs4 import BeautifulSoup                          # HTML parsing :contentReference[oaicite:1]{index=1}
from urllib.parse import urljoin                       # build absolute URLs :contentReference[oaicite:2]{index=2}

BASE_URL = "https://in.mathworks.com"
START_PATH = "/help/slrealtime/ug/troubleshooting-basics.html"
EXTRA = "/help/slrealtime/ug/"


def fetch_soup(path: str) -> BeautifulSoup:
    """Fetches a URL path and returns its BeautifulSoup-parsed HTML."""
    resp = requests.get(urljoin(BASE_URL, path))
    resp.raise_for_status()                              # error on bad status :contentReference[oaicite:3]{index=3}
    return BeautifulSoup(resp.text, "html.parser")


def get_categories_and_links(soup: BeautifulSoup) -> dict[str, list[str]]:
    """
    Returns a dict mapping each category heading to a list of its sub-page URLs.
    """
    # 1. Find the <h2> containing “Troubleshooting Basics”
    ts_h2 = soup.find(
        lambda tag: tag.name == "h2" and "Troubleshooting Basics" in tag.get_text()
    )                                                   # match by text :contentReference[oaicite:4]{index=4}
    # 2. Ascend to its enclosing <section>
    section = ts_h2.find_parent("section")              # climb parse-tree :contentReference[oaicite:5]{index=5}

    categories: dict[str, list[str]] = {}
    # 3. For each top-level <li> under div.itemizedlist, extract category & links
    for li in section.select("div.itemizedlist > ul > li"):  # CSS nested select :contentReference[oaicite:6]{index=6}
        cat_name = li.find("p").get_text(strip=True)      # category heading :contentReference[oaicite:7]{index=7}
        # collect all <a> under the inner <ul>
        urls = [
            urljoin(BASE_URL + EXTRA, a["href"])
            for a in li.select("div.itemizedlist ul li a")  # nested links :contentReference[oaicite:8]{index=8}
        ]
        categories[cat_name] = urls
    return categories

# Usage
main_soup = fetch_soup(START_PATH)
categories = get_categories_and_links(main_soup)
for cat, urls in categories.items():
    print(f"{cat}: {len(urls)} links")

def extract_page_text(url: str) -> str:
    """
    Fetches a page URL and returns its concatenated title, paragraphs, and list-items.
    """
    sp = fetch_soup(url)

    # Attempt to extract a relevant title
    title_tag = sp.select_one("h1, h1.title, h2.title, title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Extract text from various commonly used content containers
    content_selectors = [
        "div.content", "article", "main", "div#main", "section", "div.article", "div.post"
    ]
    content_elements = []
    for selector in content_selectors:
        content_elements += sp.select(selector)

    # Extract paragraphs and list items
    paras, bullets = [], []
    for elem in content_elements:
        paras.extend([p.get_text(strip=True) for p in elem.find_all("p")])
        bullets.extend([li.get_text(strip=True) for li in elem.find_all("li")])

    # Deduplicate and clean
    all_text = list(dict.fromkeys([title] + paras + bullets))  # preserves order, removes duplicates
    return "\n\n".join(filter(None, all_text))


# Build mapping category → list of page texts
all_texts: dict[str, list[str]] = {}
for cat, urls in categories.items():
    texts = []
    for url in urls:
        texts.append(extract_page_text(url))              # scrape each sub‑page :contentReference[oaicite:10]{index=10}
    all_texts[cat] = texts

from langchain.text_splitter import RecursiveCharacterTextSplitter  # chunking :contentReference[oaicite:11]{index=11}
from langchain_huggingface import HuggingFaceEmbeddings            # HF embeddings :contentReference[oaicite:12]{index=12}
from langchain.vectorstores import FAISS                           # FAISS integration :contentReference[oaicite:13]{index=13}

# 4.1 Chunking setup
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# 4.2 Single embedder
embedder = HuggingFaceEmbeddings(
    model_name="intfloat/e5-base-v2",
    model_kwargs={"device": "cpu"}
)                                                           # Apache 2.0, fast & accurate :contentReference[oaicite:14]{index=14}

# 4.3 Build & save FAISS per category
for cat, pages in all_texts.items():
    # flatten all chunks for this category
    chunks = []
    for page in pages:
        chunks.extend(splitter.split_text(page))            # produce semantic chunks

    # create one FAISS index for the entire category
    store = FAISS.from_texts(
        chunks,
        embedder,
        metadatas=[{"category": cat}] * len(chunks)
    )                                                       # build vector store

    out_dir = f"backend/MainVS/faiss_{cat.replace(' ', '_').lower()}"
    store.save_local(out_dir)                               # persist index & metadata
    print(f"Saved FAISS store for '{cat}' → ./{out_dir}")

import requests                                        # HTTP requests :contentReference[oaicite:0]{index=0}
from bs4 import BeautifulSoup, Tag                          # HTML parsing :contentReference[oaicite:1]{index=1}
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

# def extract_page_text(url: str) -> str:
#     """
#     Fetches a page URL and returns its concatenated title, paragraphs, and list-items.
#     """
#     sp = fetch_soup(url)

#     # Attempt to extract a relevant title
#     title_tag = sp.select_one("h1, h1.title, h2.title, title")
#     title = title_tag.get_text(strip=True) if title_tag else ""

#     # Extract text from various commonly used content containers
#     content_selectors = [
#         "div.content", "article", "main", "div#main", "section", "div.article", "div.post"
#     ]
#     content_elements = []
#     for selector in content_selectors:
#         content_elements += sp.select(selector)

#     # Extract paragraphs and list items
#     paras, bullets = [], []
#     for elem in content_elements:
#         paras.extend([p.get_text(strip=True) for p in elem.find_all("p")])
#         bullets.extend([li.get_text(strip=True) for li in elem.find_all("li")])

#     # Deduplicate and clean
#     all_text = list(dict.fromkeys([title] + paras + bullets))  # preserves order, removes duplicates
#     return "\n\n".join(filter(None, all_text))


TAGS_TO_EXTRACT = {
    "title", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "span", "div", "pre",
    "ul", "ol", "li",
    "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    "section", "article", "main", "summary", "details",
    "figure", "figcaption",
    "label", "legend", "button", "a",
    "code", "kbd", "samp", "blockquote", "cite", "mark", "abbr", "time"
}

TAGS_TO_IGNORE = {"script", "style", "template", "meta", "link", "base", "noscript"}

def extract_structured_text_only(tag: Tag) -> list[dict]:
    """
    Recursively extract structured text from a BeautifulSoup Tag, excluding tag names.
    Returns:
        A list of {'text': ..., 'children': [...]}
    """
    results = []
    for child in tag.children:
        if isinstance(child, Tag):
            if child.name in TAGS_TO_IGNORE:
                continue
            element = {
                "text": child.get_text(strip=True) if child.name in TAGS_TO_EXTRACT else "",
                "children": extract_structured_text_only(child)
            }
            if element["text"] or element["children"]:
                results.append(element)
    return results

def parse_html_to_nested_text_structure(url: str) -> list[dict]:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return extract_structured_text_only(soup)



# Build mapping category → list of page texts
all_texts: dict[str, list[str]] = {}
for cat, urls in categories.items():
    texts = []
    for url in urls:
        texts.append(parse_html_to_nested_text_structure(url))              # scrape each sub‑page :contentReference[oaicite:10]{index=10}
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
) # Apache 2.0, fast & accurate :contentReference[oaicite:14]{index=14}                                       

# ——————————————————————————————————————————————————————————————————————————
# utility to turn your nested {"text":…, "children":[…]} into one string
def flatten_structured_text(struct: list[dict]) -> str:
    """
    Recursively walks your nested list-of-dicts and
    concatenates all 'text' fields in document order.
    """
    lines = []
    for node in struct:
        txt = node.get("text", "")
        if txt:
            lines.append(txt)
        # recurse into children
        if node.get("children"):
            lines.append(flatten_structured_text(node["children"]))
    return "\n".join(lines)

# … later, in your FAISS‑building loop …
for cat, pages in all_texts.items():
    chunks = []
    for page_struct in pages:
        # flatten the nested dict→string
        page_text = flatten_structured_text(page_struct)
        # now split_text will get a string, not a list
        chunks.extend(splitter.split_text(page_text))

    # proceed to embed & save as before
    store = FAISS.from_texts(
        chunks,
        embedder,
        metadatas=[{"category": cat}] * len(chunks)
    )
    out_dir = f"backend/MainVS/faiss_{cat.replace(' ', '_').lower()}"
    store.save_local(out_dir)
    print(f"Saved FAISS store for '{cat}' → ./{out_dir}")

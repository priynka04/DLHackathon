import requests                                        # HTTP requests :contentReference[oaicite:0]{index=0}
from bs4 import BeautifulSoup, Tag                      # HTML parsing :contentReference[oaicite:1]{index=1}
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
#     Fetches a page URL and returns only the text within
#     <section itemprop="content">…</section>, preserving order.
#     """
#     sp = fetch_soup(url)

#     # 1. Locate all sections marked as main content
#     content_secs = sp.find("section", {"itemprop": "content"})  # microdata filter :contentReference[oaicite:3]{index=3}

#     texts: list[str] = []
#     # 2. Within each section, pull only semantic tags
#     for sec in content_secs:
#         # We choose headings, paragraphs, list-items, code, and blockquotes
#         for tag in sec.find_all(["h2","h3","h4","p","li","pre","code","blockquote"]):  # CSS selectors by tag :contentReference[oaicite:4]{index=4}
#             txt = tag.get_text(separator=" ", strip=True)
#             if txt:
#                 texts.append(txt)

#     # 3. Join in order, separated by blank lines
#     return "\n\n".join(texts)

def extract_page_text(url: str) -> str:
    """
    Fetches a page URL and returns its content as Markdown,
    properly handling headers, nested sections, paragraphs, and code blocks.
    """
    sp = fetch_soup(url)
    if not sp:
        return ""

    content_secs = sp.find_all("section", {"itemprop": "content"})
    md_lines: list[str] = []

    def walk(node):
        if not isinstance(node, Tag):
            return

        # if node.name in ("h2", "h3", "h4"):
        #     level = int(node.name[1])
        #     text = node.get_text(" ", strip=True)
        #     md_lines.append(f"{'#' * level} {text}")
        if node.name in ("h2","h3"):
        # real headers we split on
            level = int(node.name[1])
            text = node.get_text(" ", strip=True)
            md_lines.append(f"{'#'*level} {text}")
        elif node.name == "h4":
            # render H4 as bold paragraph so it stays inside H3 chunk
            text = node.get_text(" ", strip=True)
            if text:
                md_lines.append(f"**{text}**")
        elif node.name == "p":
            # Handle inline code inside paragraphs
            paragraph = ""
            for sub in node.descendants:
                if isinstance(sub, Tag) and sub.name == "code":
                    code_text = sub.get_text(strip=True)
                    paragraph += f"`{code_text}`"
                elif not isinstance(sub, Tag):
                    paragraph += sub.strip()
                elif sub.name == "br":
                    paragraph += "\n"
            if paragraph.strip():
                md_lines.append(paragraph.strip())
        elif node.name == "li":
            text = node.get_text(" ", strip=True)
            if text:
                md_lines.append(f"- {text}")
        elif node.name == "pre":
            code = node.get_text(strip=True)
            md_lines.append("```")
            md_lines.append(code)
            md_lines.append("```")
        elif node.name == "blockquote":
            quote = node.get_text(" ", strip=True)
            md_lines.append(f"> {quote}")
        elif node.name == "a":
            link_text = node.get_text(" ", strip=True)
            href = node.get("href", "")
            full_url = urljoin(BASE_URL, href)
            md_lines.append(f"[{link_text}]({full_url})")

        # recurse into children
        for child in node.children:
            walk(child)

    for sec in content_secs:
        walk(sec)
        
    return "\n\n".join(md_lines)


# Build mapping category → list of page texts
all_texts: dict[str, list[str]] = {}
for cat, urls in categories.items():
    if (len(categories[cat]) <= 1): continue
    # if cat != "Troubleshooting System Configuration":
    #     print(f"⚠️ Skipping '{cat}' with {len(urls)} links.")
    #     continue
    # texts = []
    # for url in urls:
    #     texts.append(extract_page_text(url))              # scrape each sub‑page :contentReference[oaicite:10]{index=10}
    # all_texts[cat] = texts
    # all_texts[cat] = [extract_page_text(url) for url in urls]
    texts = []
    for url in urls:
        md = extract_page_text(url)
        if md:
            texts.append(md)
    all_texts[cat] = texts

from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter  # chunking :contentReference[oaicite:11]{index=11}
# from langchain_text_splitters import RecursiveCharacterTextSplitter       # recursive fallback splitting
from langchain_huggingface import HuggingFaceEmbeddings            # HF embeddings :contentReference[oaicite:12]{index=12}
from langchain.vectorstores import FAISS                           # FAISS integration :contentReference[oaicite:13]{index=13}

# 4.1 Chunking setup
# splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
hdr_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "H2"), ("###", "H3")],
    strip_headers=False
)
# char_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
# embedder = HuggingFaceEmbeddings(
#     model_name="BAAI/bge-base-en-v1.5",
#     model_kwargs={"device": "cpu"}
# )



# 4.2 Single embedder
embedder = HuggingFaceEmbeddings(
    # model_name="intfloat/e5-base-v2",
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)                                                           # Apache 2.0, fast & accurate :contentReference[oaicite:14]{index=14}

# 4.3 Build & save FAISS per category
# for cat, pages in all_texts.items():
#     # flatten all chunks for this category
#     chunks = []
#     for md in pages:
#         # chunks.extend(splitter.split_text(md))            # produce semantic chunks
#         raw = splitter.split_text(md)
#         # ensure strings, not Document objects
#         for c in raw:
#             chunks.append(c.page_content if hasattr(c, 'page_content') else c)
#     if not chunks:
#         print(f"⚠️ No chunks for '{cat}', skipping.")
#         continue
#     # create one FAISS index for the entire category
#     store = FAISS.from_texts(
#         chunks,
#         embedder,
#         metadatas=[{"category": cat}] * len(chunks)
#     )                                                       # build vector store

#     out_dir = f"backend/MainVS/faiss_{cat.replace(' ', '_').lower()}"
#     store.save_local(out_dir)                               # persist index & metadata
#     print(f"Saved FAISS store for '{cat}' → ./{out_dir}")

for cat, pages in all_texts.items():
    # chunks: list[str] = []
    # for md in pages:
    #     # first pass: header-based
    #     initial = hdr_splitter.split_text(md)
    #     # ensure plain strings
    #     initial_strs = [c.page_content if hasattr(c, 'page_content') else c for c in initial]
    #     # # second pass: size control
    #     # for piece in initial_strs:
    #     #     if len(piece) > 1000:
    #     #         chunks.extend(char_splitter.split_text(piece))
    #     #     else:
    #     #         chunks.append(piece)
    #     # ── hybrid splitting with header‑prepended subchunks ──
    #     for chunk in initial_strs:
    #         # assume first line is the header
    #         lines  = chunk.split("\n")
    #         header = lines[0]
    #         body   = "\n".join(lines[1:])

    #         # recursively split the body to enforce size limits
    #         subchunks = char_splitter.split_text(body)
    #         # prepend the header to each sub‐chunk
    #         for sc in subchunks:
    #             enhanced = f"{header}\n\n{sc}"
    #             chunks.append(enhanced)
    
     # only split by Markdown headers (H2 & H3)
    chunks = []
    for md in pages:
        # this returns plain strings or Document objects
        initial = hdr_splitter.split_text(md)
        # normalize to strings
        for c in initial:
            chunks.append(c.page_content if hasattr(c, "page_content") else c)
        
    if not chunks:
        print(f"⚠️ No chunks for '{cat}', skipping.")
        continue
    store = FAISS.from_texts(
        chunks,
        embedder,
        metadatas=[{"category": cat}] * len(chunks)
    )
    out_dir = f"backend/MainVS/faiss_{cat.replace(' ', '_').lower()}"
    store.save_local(out_dir)
    print(f"Saved FAISS store for '{cat}' → ./{out_dir}")
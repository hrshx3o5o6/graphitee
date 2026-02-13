You are building PHASE 1 of a semantic article ingestion system.

Goal:
This is NOT a generic web scraper.
The goal is to extract clean, structured, semantically organized content from technical articles using PLAYWRIGHT ONLY so that later stages can build a concept graph.

Implementation language: Python.

DO NOT use BeautifulSoup or any external HTML parser.
ALL extraction must be done through Playwright DOM APIs.

====================================================================
1. TECH STACK
====================================================================

Use:
- Python 3.10+
- Playwright (sync API)
- JSON storage (mandatory)
- SQLite optional but architecture must allow it

DO NOT use:
- BeautifulSoup
- regex HTML parsing
- fragile scraping hacks
- monolithic scripts

====================================================================
2. ARCHITECTURE REQUIREMENTS
====================================================================

Use modular structure:

project/
│
├── scraper/
│   ├── browser.py        # playwright setup
│   ├── extractor.py      # DOM extraction logic
│   ├── crawler.py        # internal link crawling
│   ├── cleaner.py        # DOM filtering
│   └── section_builder.py
│
├── storage/
│   ├── models.py
│   └── json_store.py
│
├── utils/
│   └── url_utils.py
│
└── main.py

Each module must have one clear responsibility.

====================================================================
3. PLAYWRIGHT BROWSER LAYER
====================================================================

Create reusable browser manager.

Requirements:

- Launch chromium headless
- Create browser context
- Open page
- Wait for full load:

    page.wait_for_load_state("networkidle")

- Optional scrolling to trigger lazy loading
- Timeout handling

Function:

fetch_page(url: str) -> Page

Return the live Playwright page object.

====================================================================
4. EXTRACTION MUST USE PLAYWRIGHT DOM API ONLY
====================================================================

DO NOT parse raw HTML.

Use Playwright methods such as:

- page.query_selector_all()
- locator()
- evaluate()
- element_handle.inner_text()

Extraction must happen directly from DOM.

====================================================================
5. CONTENT EXTRACTION REQUIREMENTS
====================================================================

Extract:

A) Metadata
- title
- url
- timestamp
- domain

B) Semantic Content

Extract in reading order:

- h1, h2, h3, h4 headings
- paragraphs
- lists
- code blocks (pre, code)

Use DOM traversal inside Playwright.

Example approach:

- Select main/article container
- Iterate through child nodes
- Detect tag type
- Capture text content

Each block should look like:

{
  "type": "heading|paragraph|code|list",
  "tag": "h2",
  "text": "...",
  "position": 12
}

====================================================================
6. SECTION TREE BUILDING (IMPORTANT)
====================================================================

Implement heading-stack logic.

Rules:

- New heading starts a new section
- Lower-level headings become children
- Maintain reading order

Structure:

Article
 ├── H1
 │    ├── H2
 │    │    ├── H3

Section format:

{
  "section_id": "sec_1",
  "heading": "Title",
  "level": 2,
  "content_blocks": [...],
  "order_index": 5
}

DO NOT flatten text.

====================================================================
7. DOM CLEANING USING PLAYWRIGHT
====================================================================

Before extraction:

Remove or ignore:

- nav
- footer
- header
- aside
- ads
- share buttons
- scripts/styles

Prefer extraction from:

- article tag
- main tag

Fallback:
choose container with highest text density.

Use Playwright evaluate() if needed.

====================================================================
8. LINK EXTRACTION
====================================================================

Extract links ONLY inside article content.

Using Playwright:

- find all <a> elements
- get href
- normalize URLs

Rules:

- convert relative -> absolute
- remove fragments (#...)
- remove tracking params

Classify:

- internal (same domain)
- external

Store:

{
  "source_doc": "...",
  "target_url": "...",
  "anchor_text": "...",
  "is_internal": true
}

====================================================================
9. CONTROLLED CRAWLER
====================================================================

Implement:

crawl(root_url, depth=1, max_pages=5)

Rules:

- same domain only
- visited set required
- enforce max depth
- enforce max pages

DO NOT crawl entire website.
Only contextual linked pages.

Each crawled page should preserve:

- parent_url
- depth

====================================================================
10. DATA MODELS (MANDATORY)
====================================================================

Document:

Document:
    id
    url
    title
    depth
    parent_url
    sections[]
    links[]

Section:

Section:
    section_id
    heading
    level
    content_blocks
    order_index

Link:

Link:
    source_doc_id
    target_url
    anchor_text
    is_internal

Use dataclasses or pydantic models.

====================================================================
11. STORAGE LAYER
====================================================================

JSON storage required.

Functions:

save_document(doc)
load_document(doc_id)
list_documents()

Directory:

data/docs/<doc_id>.json

Each document stored independently.

====================================================================
12. MAIN EXECUTION
====================================================================

Running:

python main.py <url>

Should:

1. Launch Playwright
2. Open root URL
3. Extract structured content
4. Extract links
5. Crawl internal links (depth controlled)
6. Save all documents

====================================================================
13. DEBUG MODE
====================================================================

Add:

--debug

Print:

- page title
- number of sections
- heading structure
- links extracted
- crawl summary

====================================================================
14. FUTURE COMPATIBILITY (VERY IMPORTANT)
====================================================================

Later stages will:

- run LLM concept extraction
- build semantic graphs
- merge multiple articles

Therefore preserve:

- hierarchy
- ordering
- section boundaries
- source traceability

====================================================================
15. CODING STYLE
====================================================================

- type hints required
- small functions
- clean logging
- no global state
- clear separation of concerns

====================================================================
END
====================================================================

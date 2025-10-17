## Quick context — what this repo is
- Single-file Python tool (`main.py`) that OCRs a PDF, builds an embeddings index (SentenceTransformers + FAISS), and answers user queries by calling Google's Gemini (via `google-generativeai`).
- Data: `data/im77-intro.pdf` is the example input. Output artifacts live under `out/` (OCR JSON, FAISS index, embeddings, metadata).

## High-level architecture (why it’s structured this way)
- OCR stage: `preprocess_and_ocr()` converts PDF pages to images (pdf2image), denoises/thresholds (OpenCV), and uses Tesseract for page-level text. Result: `out/ocr_all.json`.
- Chunking + embeddings: `build_index()` splits each page text into fixed-size chunks (CHUNK_SIZE=800), encodes with `sentence-transformers` (`all-MiniLM-L6-v2`) and stores FAISS index + embeddings + metadata under `out/index/`.
- Retrieval loop: At runtime `chat()` loads the saved index (`load_index()`), encodes the user query, retrieves top-K chunks, then calls `ask_gemini()` to produce an answer that must cite pages.

## Files to inspect for patterns and quick examples
- `main.py` — primary logic. Look here for: configuration section at the top (constants like `PDF_PATH`, `EMB_MODEL`, `CHUNK_SIZE`, `TOP_K`) and I/O paths (`out/`).
- `requirements.txt` — canonical dependency list (pdf2image, pytesseract, pillow, opencv-python-headless, sentence-transformers, faiss-cpu, google-generativeai, numpy).
- `data/im77-intro.pdf` — the sample PDF used by the script; agents should assume `data/` contains inputs.

## Developer workflows & commands (what to run)
- Create a virtualenv and install deps: prefer pip in a modern Python 3.10+ environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Required external binaries/environment:
  - Tesseract OCR must be installed on the system and accessible in PATH (pytesseract is a Python wrapper). On macOS use Homebrew: `brew install tesseract`.
  - `poppler` toolchain is required by `pdf2image` to convert PDFs: `brew install poppler`.
  - Set `GOOGLE_API_KEY` in the environment for Gemini calls.

- Run the app (interactive chat):

```bash
python main.py
```

Notes: first run will create `out/ocr_all.json` and `out/index/*`. Subsequent runs will reuse them.

## Project-specific conventions and patterns
- Single-script focus: features are implemented in `main.py` rather than a package — prefer minimal, non-invasive edits (add small helper functions, keep config constants at top).
- Paths are absolute/relative and hard-coded to `OUT_DIR = "out"` and `PDF_PATH` pointing to `data/`. When changing paths, update these constants rather than sprinkling new paths elsewhere.
- Chunking strategy: fixed character-length chunks (CHUNK_SIZE). When altering retrieval behavior, adjust `CHUNK_SIZE` and `TOP_K` near the top.
- Model choices: `SentenceTransformer(EMB_MODEL)` is used synchronously; FAISS index is created with IndexFlatL2 and saved to disk. Any change to embedding dimensionality must be accompanied by rebuilding the index.

## Integration points & external dependencies
- Google Gemini: `google.generativeai` uses `GOOGLE_API_KEY`. The helper `ask_gemini()` constructs a short prompt that asks Gemini to "Answer based only on the text below and cite pages." Keep prompt edits conservative — the code expects a `.text` attribute on the returned object.
- FAISS: index file `out/index/faiss.index` and `out/index/embs.npy` must be consistent. Rebuild the index if you change the embedding model.
- Tesseract & Poppler: OCR and pdf conversion are native dependencies; failing to install them is the most common source of runtime errors.

## Small, actionable rules for AI agents editing this repo
1. Preserve top-level constants and their names (`PDF_PATH`, `OUT_DIR`, `DPI`, `EMB_MODEL`, `CHUNK_SIZE`, `TOP_K`) unless you also update all callers and explain why.
2. If you change the embedding model or its dimension, add an explicit index-rebuild step and guard existing index loads with version checks (store model name in `meta.json`).
3. Any change that affects on-disk artifacts (OCR JSON, embeddings, FAISS index, texts/meta files) must include a migration path (rebuild script or clear instructions in comments).
4. Keep the interactive `chat()` loop behavior predictable: return plain text to stdout and avoid adding GUI or async behavior without a corresponding README section.
5. When adding tests or CI, mock or guard calls to `google.generativeai` and external binaries (Tesseract/poppler) — do not call the real API in CI.

## Examples to copy/paste
- Rebuild index if you changed chunking or embedding model:

```python
# after updating CHUNK_SIZE or EMB_MODEL
pages = preprocess_and_ocr(PDF_PATH)
build_index(pages)
```

- How search/retrieval is expected to be used (see `retrieve()`):

```python
idx, model, texts, meta = load_index()
hits = retrieve("What is the project objective?", idx, model, texts, meta)
```

## What I couldn't discover (ask the maintainer)
- Intended deployment/CI flow (no CI files present). Ask whether answers should be cached or if Gemini usage should be rate-limited.
- Expected Python runtime version for the environment (assume 3.10+). Confirm if specific SentenceTransformers/FAISS versions are required.

---
Please review this draft and tell me if you want more detail on any section (prompts, index format, test strategy, or CI setup). I can expand or merge changes if you have an existing `.github/copilot-instructions.md` to preserve.

import os, json, numpy as np
import sys
from pdf2image import convert_from_path
from PIL import Image
import cv2, pytesseract
from pytesseract import Output
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
import google.api_core.exceptions as gexc

# ======= CONFIG =======
PDF_PATH = "/Users/karthikgshanm/Documents/im77chat/data/im77-intro.pdf"
OUT_DIR = "out"
DPI = 300
EMB_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
TOP_K = 3
API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    print("ERROR: environment variable GOOGLE_API_KEY is not set.\nSet it with: export GOOGLE_API_KEY=your_key and retry.")
    sys.exit(1)
genai.configure(api_key=API_KEY)

# Check native binaries used by the pipeline
def _which(cmd):
    from shutil import which
    return which(cmd)

missing_bins = []
if not _which("tesseract"):
    missing_bins.append("tesseract")
if not _which("pdftoppm"):
    missing_bins.append("pdftoppm (poppler)")
if missing_bins:
    print("ERROR: Required native binaries missing:", ", ".join(missing_bins))
    print("On macOS install with Homebrew:\n  brew install tesseract poppler")
    print("On Linux (Debian/Ubuntu):\n  sudo apt update && sudo apt install -y tesseract-ocr poppler-utils")
    sys.exit(1)
# =======================

os.makedirs(f"{OUT_DIR}/index", exist_ok=True)

def preprocess_and_ocr(pdf_path):
    pages = convert_from_path(pdf_path, dpi=DPI)
    all_pages = []
    for i, page in enumerate(pages, 1):
        gray = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2GRAY)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(th)
        all_pages.append({"page": i, "text": text})
    with open(f"{OUT_DIR}/ocr_all.json", "w", encoding="utf-8") as f:
        json.dump(all_pages, f, ensure_ascii=False, indent=2)
    return all_pages

def build_index(pages):
    model = SentenceTransformer(EMB_MODEL)
    texts, meta = [], []
    for p in pages:
        text = p["text"].replace("\n", " ")
        for i in range(0, len(text), CHUNK_SIZE):
            chunk = text[i:i+CHUNK_SIZE].strip()
            if chunk:
                texts.append(chunk)
                meta.append({"page": p["page"]})
    embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    idx = faiss.IndexFlatL2(embs.shape[1])
    idx.add(embs)
    faiss.write_index(idx, f"{OUT_DIR}/index/faiss.index")
    np.save(f"{OUT_DIR}/index/embs.npy", embs)
    with open(f"{OUT_DIR}/index/meta.json", "w") as f:
        json.dump(meta, f)
    with open(f"{OUT_DIR}/index/texts.json", "w") as f:
        json.dump(texts, f)
    print("Index built:", len(texts), "chunks")

def load_index():
    idx = faiss.read_index(f"{OUT_DIR}/index/faiss.index")
    embs = np.load(f"{OUT_DIR}/index/embs.npy")
    with open(f"{OUT_DIR}/index/meta.json") as f: meta = json.load(f)
    with open(f"{OUT_DIR}/index/texts.json") as f: texts = json.load(f)
    model = SentenceTransformer(EMB_MODEL)
    return idx, model, texts, meta

def retrieve(query, idx, model, texts, meta, k=TOP_K):
    q_emb = model.encode([query])
    D, I = idx.search(q_emb, k)
    return [{"page": meta[i]["page"], "text": texts[i]} for i in I[0]]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

def ask_gemini(context, question):
    """Call Gemini (configurable via GEMINI_MODEL). On failure, return a helpful fallback string.

    The function returns a plain string. If the configured model isn't available the function
    catches the error and returns a diagnostic message that includes a short context excerpt.
    """
    prompt = f"Answer based only on the text below and cite pages.\n\nContext:\n{context}\n\nQuestion:\n{question}"
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(prompt)
        # Some client implementations return an object with .text
        return getattr(resp, "text", str(resp))
    except gexc.NotFound as e:
        msg = (
            f"GENAI MODEL NOT FOUND: {GEMINI_MODEL}.\n"
            "Check available models (ListModels) or set GEMINI_MODEL to a supported model name.\n"
            f"Error detail: {e}\n\n"
            "FALLBACK: returning short context excerpt instead of model output."
        )
        print(msg)
        return f"[GENAI UNAVAILABLE - Fallback answer]\n{context[:1000]}"
    except Exception as e:
        print(f"GENAI ERROR: {e}")
        return f"[GENAI ERROR] {e}\n{context[:500]}"

def chat():
    idx, model, texts, meta = load_index()
    print("\n📘 Ready. Ask questions about your PDF (Ctrl+C to quit).")
    while True:
        try:
            q = input("\nQ: ").strip()
            if not q: continue
            hits = retrieve(q, idx, model, texts, meta)
            context = "\n\n".join([f"[page {h['page']}] {h['text']}" for h in hits])
            ans = ask_gemini(context, q)
            print("\nA:", ans)
        except KeyboardInterrupt:
            print("\nBye.")
            break

if __name__ == "__main__":
    if not os.path.exists(f"{OUT_DIR}/ocr_all.json"):
        pages = preprocess_and_ocr(PDF_PATH)
        build_index(pages)
    else:
        with open(f"{OUT_DIR}/ocr_all.json") as f:
            pages = json.load(f)
        if not os.path.exists(f"{OUT_DIR}/index/faiss.index"):
            build_index(pages)
    chat()

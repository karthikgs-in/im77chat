import os
import streamlit as st
from pathlib import Path

# Import pipeline functions from main.py
from main import preprocess_and_ocr, build_index, load_index, retrieve, ask_gemini, OUT_DIR, PDF_PATH


st.set_page_config(page_title="PDF QA (im77chat)", layout="wide")

st.title("PDF Question Answering — im77chat")

data_dir = Path("data")
uploaded = st.file_uploader("Upload a PDF (optional, only used if you rebuild the index)", type=["pdf"] )

rebuild_pdf_path: str | None = None
if uploaded:
    dest = data_dir / uploaded.name
    with open(dest, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"Saved to {dest}")
    rebuild_pdf_path = str(dest)

# Prefer loading an existing index. Only run OCR/build when the user requests it.
index_file = Path(OUT_DIR) / "index" / "faiss.index"
idx = model = texts = meta = None
index_loaded = False
if index_file.exists():
    try:
        idx, model, texts, meta = load_index()
        index_loaded = True
        st.success("Loaded existing index from out/index/")
    except Exception as e:
        st.error(f"Failed to load existing index: {e}")

if st.button("(Re)build index from PDF"):
    # Use uploaded PDF if provided for rebuild, otherwise fall back to configured PDF_PATH
    pdf_to_use = rebuild_pdf_path or PDF_PATH
    if not pdf_to_use:
        st.error("No PDF available to build from. Upload a PDF or set PDF_PATH in the repo.")
    else:
        with st.spinner("Running OCR and building index (this may take a while)..."):
            pages = preprocess_and_ocr(pdf_to_use)
            build_index(pages)
        st.success("Index built; reloading")
        try:
            idx, model, texts, meta = load_index()
            index_loaded = True
            st.success("Index reloaded")
        except Exception as e:
            st.error(f"Index built but failed to reload: {e}")

q = st.text_input("Ask a question about the PDF")
if q and st.button("Ask"):
    if not index_loaded:
        st.error("No index loaded. Please build the index first or upload an index to out/index/.")
    else:
        with st.spinner("Retrieving and querying model..."):
            hits = retrieve(q, idx, model, texts, meta)
            context = "\n\n".join([f"[page {h['page']}] {h['text']}" for h in hits])
            ans = ask_gemini(context, q)
        st.subheader("Answer")
        st.write(ans)
        st.subheader("Retrieved hits")
        for h in hits:
            st.write(f"Page {h['page']}: ")
            st.write(h['text'])

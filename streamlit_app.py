import os
import streamlit as st
from pathlib import Path

# Import pipeline functions from main.py
from main import preprocess_and_ocr, build_index, load_index, retrieve, ask_gemini, OUT_DIR, PDF_PATH


st.set_page_config(page_title="PDF QA (im77chat)", layout="wide")

st.title("PDF Question Answering — im77chat")

data_dir = Path("data")
uploaded = st.file_uploader("Upload a PDF", type=["pdf"] )

if uploaded:
    dest = data_dir / uploaded.name
    with open(dest, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"Saved to {dest}")
    pdf_path = str(dest)
else:
    pdf_path = PDF_PATH
    st.info(f"Using sample PDF: {pdf_path}")

if st.button("(Re)build index"):
    with st.spinner("Running OCR and building index (this may take a while)..."):
        pages = preprocess_and_ocr(pdf_path)
        build_index(pages)
    st.success("Index built")

if Path(OUT_DIR, "index", "faiss.index").exists():
    idx, model, texts, meta = load_index()
    st.success("Index loaded")
else:
    st.warning("Index not found. Run (Re)build index first.")

q = st.text_input("Ask a question about the PDF")
if q and st.button("Ask"):
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

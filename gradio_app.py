import gradio as gr
from typing import List, Tuple

from main import load_index, retrieve, ask_gemini


def safe_load_index():
    try:
        return load_index()
    except Exception as e:
        print(f"Failed to load index at startup: {e}")
        return None, None, None, None


idx, model, texts, meta = safe_load_index()


def respond(user_message: str, history: List[Tuple[str, str]]):
    history = history or []
    if idx is None:
        bot_reply = "Index not available on server. Please upload or build the index."
        history.append((user_message, bot_reply))
        return history

    # Retrieve relevant chunks
    hits = retrieve(user_message, idx, model, texts, meta)
    context = "\n\n".join([f"[page {h['page']}] {h['text']}" for h in hits])

    # Call Gemini via ask_gemini (handles lazy imports and fallbacks)
    answer = ask_gemini(context, user_message)
    history.append((user_message, answer))
    return history


with gr.Blocks(title="im77chat - Gradio") as demo:
    gr.Markdown("# im77chat — PDF Q&A (Gradio)")
    chatbot = gr.Chatbot()
    with gr.Row():
        txt = gr.Textbox(show_label=False, placeholder="Ask about the PDF...")
        btn = gr.Button("Send")

    txt.submit(respond, [txt, chatbot], chatbot)
    btn.click(respond, [txt, chatbot], chatbot)


if __name__ == "__main__":
    demo.launch()

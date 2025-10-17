# list_gemini_models.py
import os
import google.generativeai as genai

# make sure you've set your key
# export GOOGLE_API_KEY="your_api_key"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Fetching available Gemini models...\n")
models = genai.list_models()

for m in models:
    name = m.name
    supports = []
    if getattr(m, "supported_generation_methods", None):
        supports = m.supported_generation_methods
    print(f"🧠 {name}")
    print(f"   Supported: {', '.join(supports) if supports else '—'}\n")

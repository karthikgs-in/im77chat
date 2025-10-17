# Deploying im77chat to Streamlit Cloud

Quick steps

1. Push your repo to GitHub (already done).
2. On Streamlit Cloud, create a new app and connect it to this repository and the `main` branch.
3. In the app settings, add a secret for the Gemini key:

   - Key: `GOOGLE_API_KEY`
   - Value: your API key

4. Optional: set `GEMINI_MODEL` in Secrets (e.g., `gemini-2.5-pro`).

Protobuf runtime error and how to fix it

You may see the error:

```
TypeError: Descriptors cannot be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
```

This is caused by incompatible `protobuf` versions installed by Streamlit Cloud or other dependencies. Fixes:

- Preferred: pin `protobuf==3.20.3` in `requirements.txt` (already included) and push — Streamlit Cloud will reinstall dependencies.
- Alternative (less ideal): set the environment variable `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` in the app settings (slower parsing).

Secrets and local development

- Locally, create `~/.streamlit/secrets.toml` with:

  ```toml
  GOOGLE_API_KEY = "your_api_key_here"
  GEMINI_MODEL = "gemini-2.5-pro"
  ```

- Don't commit `secrets.toml`. Add `.streamlit/secrets.toml` to `.gitignore` if necessary.

Troubleshooting

- If Streamlit fails during dependency install, check build logs for protobuf/pyarrow/numpy conflicts. Use an isolated environment for local testing.
- If the app starts but the Gemini model returns 404, set `GEMINI_MODEL` to a supported model name for your API key.

---

## Deploying to Hugging Face Spaces (Streamlit)

Hugging Face Spaces can host Streamlit apps and lets you install system packages via `apt.txt`.

1. Create a new Space on Hugging Face and select "Streamlit" as the runtime.
2. In the Space repo settings, enable "Hardware > CPU" (unless you need GPU and have access).
3. Add these files from this repo to the Space (repo already contains them):
  - `requirements.txt` (runtime deps)
  - `apt.txt` (system packages: tesseract-ocr, poppler-utils)
  - `streamlit_app.py`, `main.py`, and the rest of the repo files.
4. Set the required Secrets in the Space (Settings -> Secrets):
  - `GOOGLE_API_KEY` — your Gemini API key
  - Optionally `GEMINI_MODEL` — e.g. `gemini-2.5-pro` (only if supported by your key)

Notes:
- HF Spaces runs `apt-get update && apt-get install -y $(cat apt.txt)` to install system packages listed in `apt.txt`.
- The repo includes an `imghdr` shim and a small local package to avoid missing-stdlib issues that have appeared in hosted runtimes.
- If you plan to avoid installing heavy ML packages on the Space, use the trimmed `requirements.txt` (this repo already separates heavy deps into `requirements-dev.txt`).

If you want, I can (a) add an upload button to the Streamlit app to accept a prebuilt `out/index/` zip, or (b) create a minimal `space` repository template and push it for you.

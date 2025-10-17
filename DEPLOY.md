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

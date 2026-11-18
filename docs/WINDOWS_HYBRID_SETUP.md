# Windows 10 hybrid foundation setup

This optional service uses external Python 3.11. Keep it separate from Abaqus
2023's bundled Python 2.7.15. Existing RAG/Ollama remains available through
`src.api.main`; this first hybrid foundation starts separately on port 8001.

1. Install 64-bit Python 3.11 and create a virtual environment in the repo.
2. Install the existing `requirements.txt` into that environment.
3. Copy `.env.example` to `.env`, then set a random `ABAQUSGPT_API_TOKEN` of
   at least 32 characters and your `OPENAI_API_KEY`. Keep `.env` private and
   never commit it.
4. In PowerShell, activate the environment and run:

   ```powershell
   python -m uvicorn src.hybrid.main:app --host 127.0.0.1 --port 8001
   ```

5. Send `Authorization: Bearer <ABAQUSGPT_API_TOKEN>` on `/chat` and `/bridge/*`
   requests. CORS permits only the listed localhost origins. Keep the host on
   `127.0.0.1` for local use.
6. Run the safety tests with `python -m unittest discover -s tests`.

The Python 2.7.15-compatible contract in `abaqus_scripts/bridge_contract.py`
only validates serialized envelopes. The bridge currently validates and records requests in memory only. Approval
marks a request `approved_for_operator_review`; it does not alter a model or
submit a job. No shell, Python, Abaqus command, or arbitrary code execution
operation exists. A future Abaqus adapter must live in a separate Python
2.7.15-compatible script directory and implement only reviewed operations.
This foundation has not been tested inside Abaqus.


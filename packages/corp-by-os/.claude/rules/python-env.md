# Python Environment — corp-by-os

- Python >=3.11, target 3.12
- Virtual env: .venv\Scripts\Activate.ps1
- Install: pip install -e ".[dev,llm]"
- This is the ROOT ORCHESTRATOR — it calls CKE, CPE, COM via subprocess
- Dataclasses not Pydantic (lightweight, frozen where appropriate)
- Index lives in %LOCALAPPDATA%, never OneDrive
- corp-os-meta is a direct dependency (import, not subprocess)

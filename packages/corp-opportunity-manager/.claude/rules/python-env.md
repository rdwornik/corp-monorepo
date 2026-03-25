# Python Environment — corp-opportunity-manager

- Python >=3.10, target 3.12
- Virtual env: .venv\Scripts\Activate.ps1
- Install: pip install -e ".[dev,llm]"
- Click CLI entry point: `com`
- Reads Project_Codes.xlsm from 90_System/ (shared with SCA)
- Gemini Flash for intent routing (optional)

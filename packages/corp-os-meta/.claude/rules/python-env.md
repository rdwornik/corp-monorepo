# Python Environment — corp-os-meta

- Python >=3.11, target 3.12
- Virtual env: .venv\Scripts\Activate.ps1
- Install: pip install -e ".[dev]" (when dev extras exist)
- This is a LIBRARY — other repos depend on it
- Zero external deps beyond: pydantic, pyyaml, click, rich, json-repair, python-dotenv
- taxonomy.yaml changes must be backward-compatible
- New required fields = schema_version bump

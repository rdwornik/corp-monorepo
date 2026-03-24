"""Smoke test: verify required API keys are available."""
import os
import pytest

# This repo is a metadata schema/taxonomy library — no API keys needed.
# If a future feature requires API access, uncomment the relevant key.
REQUIRED_KEYS = [
    # "ANTHROPIC_API_KEY",
    # "GEMINI_API_KEY",
    # "OPENAI_API_KEY",
    # "DEEPSEEK_API_KEY",
    # "XAI_API_KEY",
    # "GROQ_API_KEY",
]


@pytest.mark.parametrize("key", REQUIRED_KEYS or ["_placeholder"])
def test_api_key_available(key):
    """API key is set in environment (loaded by PS profile from global .env)."""
    if key == "_placeholder":
        pytest.skip("No API keys required by this repo")
    value = os.environ.get(key)
    assert value is not None, (
        f"{key} not found. Run 'keys list' in PowerShell. "
        f"Keys should be in Documents/.secrets/.env"
    )
    assert len(value) > 10, f"{key} too short ({len(value)} chars)"

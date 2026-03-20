# Testing Standards

- pytest for all tests, never unittest
- Test files: tests/test_*.py
- Run: py -m pytest
- Tests use tmp_path fixtures and monkeypatching — no real filesystem or API calls
- 679+ tests passing
- No silent failures — log warnings, raise on errors

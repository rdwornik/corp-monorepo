# Testing Standards

- pytest for all tests, never unittest
- Test files: tests/test_*.py
- Run: pytest tests/ -v
- Every function must have tests
- No silent failures — log warnings, raise on errors

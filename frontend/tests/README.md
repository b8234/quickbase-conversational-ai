# Frontend Tests

This directory is for frontend test files.

## Testing Streamlit Apps

Streamlit apps can be tested in several ways:

1. **Manual Testing**: Run the app and interact with it
   ```bash
   streamlit run frontend/prod.py
   ```

2. **Unit Testing**: Test individual functions
   ```bash
   pip install pytest
   pytest frontend/tests/
   ```

3. **Integration Testing**: Test with mock API responses

## What to Test

- Session state management
- Audio recording functionality
- API integration
- User input handling
- Response rendering

## Test Structure

Add your test files here following the pattern `test_*.py`

Example test file structure:
```python
import pytest
from unittest.mock import Mock, patch

def test_session_initialization():
    # Test that session state initializes correctly
    pass

def test_api_call_handling():
    # Test API integration with mocked responses
    pass
```

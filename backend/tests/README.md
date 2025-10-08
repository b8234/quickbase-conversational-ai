# Backend Tests

This directory is for backend test files and fixtures.

## Structure

- `fixtures/` - Sample data for testing (e.g., mock Quickbase responses)
- Add your test files here following the pattern `test_*.py`

## Sample Data

The `fixtures/sample_quickbase_data.json` file contains example Quickbase API responses that can be used for:
- Understanding the data structure
- Mocking API calls in tests
- Developing without live Quickbase access

## Running Tests

If you add tests, you can run them with:

```bash
# Install pytest
pip install pytest pytest-cov

# Run tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend backend/tests/
```

## Test Examples

You can create tests for:
- `quickbase_api.py` - API interactions
- `formatters.py` - Data formatting
- `field_detection.py` - Field type detection
- `cache_utils.py` - Caching logic
- `bedrock_integration.py` - Parameter extraction

Use the sample data in `fixtures/` to mock API responses.

# Contributing to Quickbase Conversational AI

Thank you for your interest in contributing to this project! This is a showcase repository demonstrating conversational AI integration with Quickbase.

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Provide clear reproduction steps
- Include relevant logs and error messages
- Specify your environment (OS, Python version, AWS region, etc.)

### Suggesting Enhancements

- Describe the enhancement in detail
- Explain the use case and benefits
- Consider backward compatibility

### Code Contributions

#### Development Setup

1. **Fork and Clone**

   ```bash
   git clone https://github.com/YOUR-USERNAME/quickbase-conversational-ai.git
   cd quickbase-conversational-ai
   ```

2. **Create a Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Environment**

   ```bash
   # Copy example environment file
   cp example.env .env
   
   # Edit .env with your values:
   # - Set DEMO_MODE=true to test without AWS backend
   # - Set DEMO_MODE=false and add API_URL for live mode
   ```

4. **Install Dependencies**

   ```bash
   # Install root dependencies
   pip install -r requirements.txt
   
   # Install component-specific dependencies
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   pip install -r lambda_frontend/requirements.txt
   ```

5. **Configure Field Allowlist**
   Edit `backend/field_allowlist.py` to match your Quickbase table structure

6. **Make Your Changes**
   - Follow existing code patterns
   - Add comments for complex logic
   - Keep functions focused and modular

7. **Test Your Changes**
   - Test frontend: `streamlit run frontend/prod.py`
   - Test backend locally with sample data from `backend/tests/fixtures/`

8. **Commit and Push**

   ```bash
   git add .
   git commit -m "Brief description of your changes"
   git push origin feature/your-feature-name
   ```

9. **Create Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Explain testing performed

## Code Style Guidelines

- **Python**: Follow PEP 8 style guide
- **Naming**: Use descriptive variable and function names
- **Comments**: Add comments for non-obvious logic
- **Docstrings**: Include for public functions
- **Line Length**: Keep under 120 characters where reasonable

## Project Structure

When adding new features, maintain the existing structure:

- `backend/` - Quickbase API and data processing
- `frontend/` - Streamlit UI
- `lambda_frontend/` - AWS Lambda handler
- `docs/` - Documentation and examples

## Testing

While comprehensive tests aren't required for this showcase repository, please:

- Manually test your changes
- Verify no existing functionality breaks
- Test with demo mode if possible
- Document any new environment variables needed

## Documentation

- Update `README.md` if adding user-facing features
- Update `architecture.md` for architectural changes
- Add inline comments for complex logic
- Update `example.env` if adding new environment variables

## Questions?

Feel free to open an issue for questions or discussions about contributing.

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Welcome newcomers and help them learn

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

# Demo Mode Guide

## Overview

Demo Mode allows you to explore and test the Quickbase Conversational AI interface without requiring AWS infrastructure or API keys.

## Configuration

Set the following in your `.env` file:

```
DEMO_MODE=true
```

## Features in Demo Mode

### ✅ Available Features
- **Full UI Access**: Complete Streamlit interface with all visual components
- **Text Input**: Test the conversational interface with sample queries
- **Voice Input**: UI controls available (actual transcription disabled)
- **Mock Responses**: Pre-defined responses that simulate real Quickbase queries
- **Session Management**: Full session state and conversation history

### ❌ Limitations
- **No AWS Integration**: Bedrock, Lambda, and Transcribe are not called
- **No Real Data**: Responses use mock data, not actual Quickbase records
- **No Voice Processing**: Transcription UI shown but not functional
- **No Backend Calls**: API Gateway endpoints are not invoked

## Use Cases

Demo Mode is ideal for:

1. **UI/UX Development**: Work on the frontend without backend dependencies
2. **Testing Layouts**: Verify responsive design and component placement
3. **Demo Presentations**: Show the interface without revealing sensitive data
4. **Contribution Testing**: Contributors can test changes without AWS access
5. **Documentation Screenshots**: Capture UI elements for documentation

## Sample Queries

When in Demo Mode, try these example queries to see mock responses:

- "Show me recent projects"
- "What are the open tasks?"
- "Find customer records from last week"
- "Export project data"

## Switching to Live Mode

To use real AWS services and Quickbase data:

1. Set `DEMO_MODE=false` in your `.env` file
2. Add `API_GATEWAY_URL` (your deployed backend endpoint)
3. Add `DEMO_API_KEY` (provided by system administrator)
4. Ensure AWS services are properly configured in the backend

See [MODE_COMPARISON.md](MODE_COMPARISON.md) for detailed differences between modes.

# Quickbase Conversational AI

> **Note**: This is a showcase repository demonstrating a conversational AI system for Quickbase. It provides complete frontend and backend code but does **not** include step-by-step deployment instructions. Use this as a reference implementation for building your own solution.

This project enables conversational access to Quickbase data using natural language, powered by Amazon Bedrock and AWS Lambda. It provides a user-friendly interface for querying, summarizing, and exporting Quickbase records, with support for both text and voice input.

## Features

- **Conversational Queries:** Ask questions about your Quickbase data using natural language.
- **Voice & Text Input:** Use the Streamlit frontend to interact by typing or speaking.
- **Quickbase Integration:** Securely fetch, filter, and summarize records from Quickbase tables.
- **Export & Attachments:** Download results and file attachments via secure S3 links.
- **Slack Notifications:** Get summaries and report links sent to Slack channels.
- **AWS Lambda & Bedrock:** Scalable backend powered by Lambda and Bedrock agent for AI responses.

## How It Works

1. **Frontend:** Users interact via a Streamlit app (text or voice).
2. **Lambda Frontend:** Handles requests, transcribes audio, and invokes the Bedrock agent.
3. **Bedrock Agent:** Processes the prompt, coordinates with backend, and generates a response.
4. **Backend:** Validates tables, runs queries, formats results, exports files, and sends notifications.
5. **Response:** Results and download links are returned to the user.

## Project Structure

- `frontend/` — Streamlit UI for user interaction
- `lambda_frontend/` — AWS Lambda handler for Bedrock agent and audio transcription
- `backend/` — Python modules for Quickbase API, data retrieval, formatting, exports, and Slack
- `backend/field_allowlist.py` — Configure which Quickbase tables and fields are accessible
- `example.env` — Template for environment variables (copy to `.env` and configure)
- `docs/` — Documentation
- `architecture.md` — System diagram and design overview

## Configuration

This project requires configuration before use:

1. **Environment Variables**: Copy `example.env` to `.env` and configure:
   - Quickbase credentials (realm, user token, app ID)
   - AWS resources (S3 bucket, region, Bedrock agent ID)
   - Slack webhook (optional)
   - API Gateway endpoint

2. **Field Allowlist**: Edit `backend/field_allowlist.py` to define:
   - Your Quickbase table names and IDs
   - Which fields users can query
   - Field markers for search, date filtering, and relationships

3. **Demo Mode**: Set `DEMO_MODE=true` in `.env` to test the frontend without AWS costs

See `architecture.md` for detailed component descriptions.


## Requirements

To run this project, you will need access to the following resources:

- **AWS IAM**: Permissions for Lambda, Bedrock agent, S3, CloudWatch, API Gateway, and Amazon Transcribe
- **Amazon Bedrock Agent**: For conversational AI responses
- **API Gateway & Lambda**: To handle frontend requests and invoke backend logic
- **Amazon Transcribe**: For audio transcription (voice input)
- **Amazon CloudWatch**: For logging and monitoring
- **Quickbase App**: Your Quickbase application with relevant tables and data
- **Slack**: For notifications and report sharing
- **Amazon S3**: For storing and sharing exported files and attachments

## System Diagram

See `architecture.md` for a visual overview of how components interact.

## What's Included

✅ **Complete source code** for frontend, backend, and Lambda functions  
✅ **Field allowlist system** for security and data control  
✅ **Demo mode** for testing without AWS infrastructure  
✅ **Environment configuration templates**  

## What's NOT Included

❌ **AWS infrastructure setup** (IAM policies, Bedrock agent configuration, API Gateway setup)  
❌ **Quickbase app creation** (you need an existing Quickbase application)  
❌ **Step-by-step deployment guide** (this is a reference implementation)  
❌ **Production hardening** (security reviews, error handling improvements, etc.)  

## Use This Repository To

- Understand how to integrate Quickbase with Amazon Bedrock
- See examples of voice-enabled AI interfaces with Streamlit
- Learn patterns for serverless conversational AI architectures
- Build your own customized Quickbase AI solution

---

For technical details and component descriptions, see `architecture.md`.

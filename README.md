# Quickbase Conversational AI

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
- `docs/` — Documentation
- `architecture.md` — System diagram and design overview


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

---

For more details, check the code and documentation in each folder.

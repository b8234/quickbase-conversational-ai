## System Architecture Diagram


```
Flowchart TD
    A[User (Streamlit Frontend)] -->|Text/Voice Input| B[Lambda Frontend]
    B -->|Transcribe Audio| C[Amazon Transcribe]
    B -->|Invoke Agent| D[Amazon Bedrock Agent]
    D -->|Query Request| E[Backend (Lambda)]
    E -->|Quickbase API| F[Quickbase]
    E -->|Export/Attachments| G[S3]
    E -->|Send Summary| H[Slack]
    E -->|Response| D
    D -->|Reply, URLs| B
    D -->|Direct Response| A
    B -->|Reply, URLs| A
```

**Legend:**
- **A:** User interacts via Streamlit UI.
- **B:** Lambda frontend handles requests, transcription, and agent invocation.
- **C:** Amazon Transcribe for voice input.
- **D:** Bedrock agent processes conversational logic and generates responses.
- **E:** Backend executes queries, formatting, exports, and notifications.
- **F:** Quickbase database.
- **G:** S3 for file exports and attachments.
- **H:** Slack for notifications.

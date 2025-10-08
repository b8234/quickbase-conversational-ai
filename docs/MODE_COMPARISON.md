# Mode Comparison: Demo vs Live

## Quick Reference

| Feature | Demo Mode | Live Mode |
|---------|-----------|-----------|
| **AWS Services** | ❌ Disabled | ✅ Fully Integrated |
| **Quickbase API** | ❌ Mock Data | ✅ Real Data |
| **Voice Input** | ❌ UI Only | ✅ Fully Functional |
| **Data Security** | N/A | ✅ Encrypted |
| **Setup Required** | Minimal | Full Infrastructure |
| **Cost** | Free | AWS Usage Fees |

## Demo Mode

### Configuration True

```env
DEMO_MODE=true
```

### Purpose (Demo Mode)

- Explore the UI without AWS infrastructure
- Test frontend changes safely
- Present the interface without sensitive data
- Allow contributors to develop without credentials

### What Works (Demo Mode)

- Complete Streamlit interface
- All UI components and layouts
- Text input fields
- Session state management
- Navigation and controls

### What's Mocked

- Bedrock AI responses
- Quickbase data queries
- Voice transcription
- Backend API calls

### Best For (Demo Mode)

- Frontend development
- UI/UX testing
- Documentation and demos
- Contribution validation

### Live Mode

### Configuration False

```env
DEMO_MODE=false
API_URL=https://your-api-gateway-url.amazonaws.com/prod
DEMO_KEY=your-provided-api-key
```

### Purpose (Live Mode)

- Production usage with real data
- Full AWS Bedrock AI capabilities
- Actual Quickbase integration
- Voice-to-text transcription

### What Works (Live Mode)

- Everything in Demo Mode, plus:
- Real Bedrock AI agent responses
- Actual Quickbase API queries
- AWS Transcribe for voice input
- Full backend Lambda integration
- S3 file storage
- Slack notifications
- CloudWatch logging

### Requirements

- Deployed AWS infrastructure
- Valid API Gateway endpoint
- Authorized API key
- AWS services configured (Lambda, Bedrock, S3, etc.)
- Quickbase credentials (backend-managed)

### Best For (Live Mode)

- Production deployments
- Real data analysis
- End-user applications
- Full feature testing

## Choosing the Right Mode

### Use Demo Mode When

- ✅ You're developing frontend features
- ✅ You don't have AWS credentials
- ✅ You want to test without costs
- ✅ You're contributing to the project
- ✅ You need to demo without sensitive data

### Use Live Mode When

- ✅ You need real Quickbase data
- ✅ You have deployed AWS infrastructure
- ✅ You've been provided an API key
- ✅ You're running in production
- ✅ You need full AI capabilities

## Transitioning Between Modes

Switching modes is as simple as updating your `.env` file:

**To Demo Mode:**

```bash
DEMO_MODE=true
# Comment out or remove Live Mode variables
```

**To Live Mode:**

```bash
DEMO_MODE=false
API_URL=https://your-api-gateway-url.amazonaws.com/prod
DEMO_KEY=your-provided-api-key
```

No code changes required - the application automatically adapts based on the `DEMO_MODE` setting.

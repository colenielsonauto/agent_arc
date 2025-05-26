# Email Router MVP

A Python prototype for an intelligent email routing system using Google's latest AI tools and OAuth2 Gmail integration.

## 🚀 Go-live Checklist (10 steps, 3 mins)

Follow these steps to get your Email Router MVP running in production:

1. **Set up virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Clean OAuth tokens** (ensures fresh scope permissions):
   ```bash
   rm -f token.json
   ```

4. **Authenticate with Gmail** (browser OAuth flow):
   ```bash
   python tools/test_gmail_auth.py
   ```

5. **Register Gmail watch** (weekly renewal required):
   ```bash
   python tools/watch_gmail.py
   ```

6. **Run smoke test** (must show all ✅):
   ```bash
   python tools/smoke_test.py
   ```

7. **Deploy Cloud Function**:
   ```bash
   gcloud functions deploy email-router-listener \
     --region=us-central1 \
     --runtime=python311 \
     --trigger-topic=email-inbound \
     --entry-point=pubsub_webhook \
     --source=. \
     --set-env-vars=GOOGLE_API_KEY=$GOOGLE_API_KEY
   ```

8. **Send test email** to `testingemailrouter@gmail.com`

9. **Check Cloud Logs** for forward/draft message IDs:
   ```bash
   gcloud functions logs read email-router-listener --limit=50
   ```

10. **🎉 Celebrate** - Your Email Router MVP is live!

## Features

- **Email Ingestion**: Process incoming emails through Pub/Sub or direct API
- **AI-Powered Classification**: Automatically categorize emails (Support, Billing, Sales)
- **Detail Extraction**: Extract key information using Google's Vertex AI
- **Smart Routing**: Forward emails to appropriate teams with AI-generated draft replies
- **OAuth2 Gmail Integration**: Secure email sending using Google OAuth2 authentication

## Setup

1. **Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Google Cloud Setup**:
   - Set up Google Cloud project
   - Enable Gmail API and Vertex AI API
   - Set `GOOGLE_API_KEY` environment variable for AI features

4. **OAuth2 Gmail Setup**:
   - Download OAuth2 credentials from Google Cloud Console
   - Save as `oauth_client.json` in project root
   - Run the application once to complete OAuth2 flow and create `token.json`

## Project Structure

```
email-router/
├── .venv/
├── requirements.txt
├── README.md
├── roles_mapping.json
├── oauth_client.json          # OAuth2 credentials (user-provided)
├── token.json                 # OAuth2 tokens (auto-generated)
├── prompts/
│   ├── classify_intent.md
│   ├── extract_details.md
│   └── draft_reply.md
├── functions/
│   ├── __init__.py
│   ├── ingest_email.py
│   ├── analyze_email.py
│   └── forward_and_draft.py   # ✨ Updated with OAuth2
├── tools/                     # ✨ New: Setup and management tools
│   ├── README.md
│   ├── watch_gmail.py         # Gmail watch registration
│   └── test_gmail_auth.py     # Authentication testing
└── test_email.json
```

## Usage

### Test the Complete Pipeline
```bash
python test_full_pipeline.py
```

### Test OAuth2 Gmail Integration Only
```bash
python test_oauth.py
```

### Test Email Ingestion Only
```bash
python -c "from functions.ingest_email import ingest_email; print(ingest_email({'data':''}, None))"
```

### Setup Gmail Watch (Real-time Processing)
```bash
# Test Gmail API authentication first
python tools/test_gmail_auth.py

# Register Gmail watch for push notifications
python tools/watch_gmail.py
```

### Run the Listener (Real-time Pipeline)

The listener processes incoming Gmail push notifications and triggers the AI pipeline.

#### Local Development
```bash
# Test the CloudEvent handler directly
python tools/smoke_test.py
```

#### Cloud Functions Deployment
```bash
# Deploy to Google Cloud Functions (2nd-gen, Pub/Sub trigger)
gcloud functions deploy email-router-listener \
  --region=us-central1 \
  --runtime=python311 \
  --trigger-topic=email-inbound \
  --entry-point=pubsub_webhook \
  --source=. \
  --set-env-vars=GOOGLE_API_KEY=$GOOGLE_API_KEY
```

#### Environment Variables (Cloud Deployment)

When deploying to Cloud Functions/Cloud Run, set these environment variables:

- `GOOGLE_API_KEY`: Required for AI classification and analysis
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key (if using service account)
```bash
# Example: Set environment variables during deployment
gcloud functions deploy email-router-listener \
  --set-env-vars=GOOGLE_API_KEY=your-api-key \
  # ... other flags
```

#### Listener Unit Tests
```bash
# Run unit tests for the listener
python -m unittest tests/test_listener.py
```

## OAuth2 Gmail Configuration

1. **Google Cloud Console Setup**:
   - Create a new project or use existing
   - Enable Gmail API
   - Create OAuth2 credentials (Desktop Application)
   - Download client secret JSON

2. **Local Setup**:
   ```bash
   # Place OAuth2 credentials in project root
   cp ~/Downloads/client_secret_*.json oauth_client.json
   
   # Run application to complete OAuth2 flow
   python test_oauth.py
   ```

3. **First Run**:
   - Browser will open for Google account authorization
   - Grant Gmail send permissions
   - `token.json` will be created automatically for future use

## Environment Variables

- `GOOGLE_API_KEY`: Required for AI classification and analysis
- OAuth2 credentials: Stored in `oauth_client.json` and `token.json`

## Renewing the Gmail Watch

Gmail watch registrations have a **7-day TTL (time-to-live)** and must be renewed regularly.

### Manual Renewal
```bash
python tools/watch_gmail.py  # Re-register watch before expiration
```

### Automated Renewal (TODO)
For production deployments, consider setting up automated renewal:

1. **Cloud Scheduler**: Create a weekly cron job to call watch registration
2. **Cloud Function**: Implement watch renewal endpoint
3. **Monitoring**: Set up alerts for watch expiration

```yaml
# Example Cloud Scheduler job (TODO)
name: gmail-watch-renewal
schedule: "0 0 * * 0"  # Weekly on Sunday at midnight
target:
  httpTarget:
    uri: https://your-function-url/renew-watch
```

⚠️ **Important**: If the watch expires, new emails will not trigger the pipeline until renewed.

## Secret Manager (Optional)

For production deployments, consider using Google Secret Manager for `token.json`:

1. **Create secret**:
   ```bash
   gcloud secrets create gmail-oauth-token --data-file=token.json
   ```

2. **Deploy with secret**:
   ```bash
   gcloud functions deploy email-router-listener \
     --set-secrets=GMAIL_TOKEN=gmail-oauth-token:latest \
     # ... other flags
   ```

3. **Update code** to read from environment variable instead of file.

## Features & Fallbacks

The system includes graceful fallbacks for development and testing:

- **AI Analysis**: Uses mock responses if `GOOGLE_API_KEY` not set
- **Gmail Sending**: Uses mock responses if OAuth2 not configured
- **Error Handling**: Comprehensive error handling with detailed logging

## Next Steps

1. Configure Google Cloud credentials
2. Set up OAuth2 for Gmail API
3. Deploy to Google Cloud Functions 
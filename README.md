# Email Router MVP

A Python prototype for an intelligent email routing system using Google's latest AI tools.

## Features

- **Email Ingestion**: Process incoming emails through Pub/Sub or direct API
- **AI-Powered Classification**: Automatically categorize emails (Support, Billing, Sales)
- **Detail Extraction**: Extract key information using Google's Vertex AI
- **Smart Routing**: Forward emails to appropriate teams with AI-generated draft replies

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
   - Enable Vertex AI API
   - Configure authentication (service account key)

## Project Structure

```
email-router/
├── .venv/
├── requirements.txt
├── README.md
├── roles_mapping.json
├── prompts/
│   ├── classify_intent.md
│   ├── extract_details.md
│   └── draft_reply.md
├── functions/
│   ├── __init__.py
│   ├── ingest_email.py
│   ├── analyze_email.py
│   └── forward_and_draft.py
└── test_email.json
```

## Usage

Test the email ingestion:
```bash
python -c "from functions.ingest_email import ingest_email; print(ingest_email({'data':''}, None))"
```

## Next Steps

1. Configure Google Cloud credentials
2. Implement Vertex AI integration
3. Set up Pub/Sub topics
4. Add email forwarding logic
5. Deploy to Google Cloud Functions 
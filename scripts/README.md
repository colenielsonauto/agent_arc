# Email Router MVP - Tools

CLI tools for setting up and managing the Email Router MVP system.

## 📧 Gmail Watch Registration

### `watch_gmail.py`

Registers Gmail watch on the inbox to send push notifications to Pub/Sub topic for real-time email processing.

#### Prerequisites

1. **Google Cloud Project Setup**:
   - Project: `email-router-460622`
   - Gmail API enabled
   - Pub/Sub topic `email-inbound` exists (✅ confirmed)

2. **OAuth2 Credentials**:
   - Valid `oauth_client.json` in project root
   - OAuth2 client configured for Desktop Application
   - Scopes: `gmail.send` + `gmail.readonly`

3. **Pub/Sub Permissions**:
   - Topic: `projects/email-router-460622/topics/email-inbound`
   - Gmail API service account needs publish permissions:
     ```
     gmail-api-push@system.gserviceaccount.com
     ```

#### Usage

```bash
# From project root
python tools/watch_gmail.py
```

#### What it does

1. **Authenticates** with Gmail API using OAuth2
2. **Registers** Gmail watch on INBOX
3. **Configures** push notifications to Pub/Sub topic
4. **Reports** watch status and expiration

#### Expected Output

```
============================================================
📧 Gmail Watch Registration Tool
============================================================

1. 🔐 Authenticating with Gmail API...
✅ Gmail API authentication successful!
👤 Connected as: testingemailrouter@gmail.com

2. 📡 Registering Gmail watch...
   📮 Target: INBOX
   🔔 Pub/Sub Topic: projects/email-router-460622/topics/email-inbound
✅ Gmail watch registered successfully!
   📊 History ID: 12345
   ⏰ Expiration: 604800000
   📅 Expires: 2024-01-08 14:30:00

🎉 Gmail Watch Setup Complete!
```

#### Troubleshooting

##### OAuth2 Issues
```
❌ OAuth flow failed: (invalid_client) Unauthorized
```
**Solution**: 
- Verify `oauth_client.json` contains valid Google Cloud OAuth2 credentials
- Ensure OAuth2 client is configured for "Desktop Application"
- Check that Gmail API is enabled in Google Cloud Console

##### Pub/Sub Permission Issues
```
❌ Failed to register Gmail watch: topic permission denied
```
**Solution**:
- Verify Pub/Sub topic exists: `projects/email-router-460622/topics/email-inbound`
- Add IAM permission for `gmail-api-push@system.gserviceaccount.com`:
  ```bash
  gcloud pubsub topics add-iam-policy-binding email-inbound \
    --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
    --role=roles/pubsub.publisher
  ```

#### Watch Lifecycle

- **Duration**: 7 days (Google's maximum)
- **Renewal**: Must be re-registered weekly
- **Monitoring**: Check Pub/Sub topic for incoming messages

#### Next Steps

Once Gmail watch is registered:

1. **Implement Pub/Sub subscriber** to process notifications
2. **Create Cloud Function** or **Pull subscription** to handle messages
3. **Test** by sending email to `testingemailrouter@gmail.com`
4. **Monitor** Pub/Sub topic for incoming notifications

## Development Notes

### Scope Changes

If you modify Gmail API scopes:
1. Delete existing `token.json`
2. Re-run OAuth2 flow
3. Update all scripts using Gmail API

### Production Deployment

For production:
1. Use service account authentication instead of OAuth2
2. Set up automated watch renewal (7-day lifecycle)
3. Implement proper error handling and monitoring 
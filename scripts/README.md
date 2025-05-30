# 🛠️ Development Scripts

This directory contains utility scripts for testing, development, and system management.

## 🧪 Current Active Scripts

### **Core Testing Scripts**

#### `test_ai_integration.py`
**Comprehensive AI and API testing**
```bash
python scripts/test_ai_integration.py
```
Tests AI classification, FastAPI integration, and health endpoints.

#### `test_mailgun_simple.py`
**Mailgun email functionality testing**
```bash
python scripts/test_mailgun_simple.py
```
Tests Mailgun API connection, email sending, and validation.

#### `test_mailgun_authorized.py`
**Mailgun sandbox recipient management**
```bash
python scripts/test_mailgun_authorized.py
```
Adds authorized recipients for sandbox domain testing.

## 🔧 Legacy Scripts (Reference)

These scripts are from the previous architecture but contain useful patterns:

- `test_gmail_auth.py` - Gmail OAuth2 authentication
- `watch_gmail.py` - Gmail watch registration for Pub/Sub
- `smoke_test.py` - System health testing
- `test_new_architecture.py` - Architecture validation

## 📚 More Information

For detailed development workflows, testing strategies, and debugging guides, see:
- **[Development Guide](../docs/DEVELOPMENT.md)** - Complete development workflow
- **[Architecture Guide](../docs/ARCHITECTURE.md)** - Technical architecture details
- **[Main README](../README.md)** - Project overview and quick start

## Quick Usage

```bash
# Test everything is working
python scripts/test_ai_integration.py

# Test email sending
python scripts/test_mailgun_simple.py

# Start development server
cd src/api && python main.py

# Check API docs
open http://localhost:8000/docs
``` 
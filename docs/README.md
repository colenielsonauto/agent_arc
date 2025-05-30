# 📚 Email Router Documentation

## Quick Navigation

### 🚀 **Getting Started**
- **[Main README](../README.md)** - Project overview, quick start, and features
- **[Development Guide](./DEVELOPMENT.md)** - Complete setup and development workflow

### 🏗️ **Technical Details**
- **[Architecture Guide](./ARCHITECTURE.md)** - System design, patterns, and implementation
- **[Project Structure](./PROJECT_STRUCTURE.md)** - File organization and cleanup guide

### 🛠️ **Development**
- **[Scripts Guide](../scripts/README.md)** - Testing and utility scripts

### 📖 **Specialized Guides**
- **[Mailgun Integration](./MAILGUN_INTEGRATION.md)** - Email sending setup and testing
- **[Security Guide](./SECURITY_AND_CREDENTIALS_GUIDE.md)** - Security and credential management

## Documentation Philosophy

### 📖 **One Source of Truth**
Each topic has **one primary document** to avoid confusion and duplication:

- **README.md** (root) - Project overview and quick start
- **DEVELOPMENT.md** - Everything about development workflow
- **ARCHITECTURE.md** - Technical system design
- **Scripts** - Focused on script usage only

### 🎯 **User-Focused Organization**
Documentation is organized by **what you want to do**:

- **New to the project?** → Start with main README.md
- **Want to develop?** → Follow DEVELOPMENT.md
- **Need technical details?** → See ARCHITECTURE.md
- **Having issues?** → Check relevant guide

### ✅ **Kept Current**
Documentation reflects the **current system state**:
- ✅ Updated for Claude AI integration
- ✅ Reflects clean project structure
- ✅ Shows working FastAPI server
- ✅ Includes real test results
- ✅ Cleaned up outdated documentation

## Quick Start for Developers

```bash
# 1. Read the main README for overview
open ../README.md

# 2. Follow development setup
open ./DEVELOPMENT.md

# 3. Test everything works
python scripts/test_ai_integration.py

# 4. Start building!
cd src/api && python main.py
open http://localhost:8000/docs
```

## Contributing to Documentation

### 📝 **When to Update**
- Adding new features or components
- Changing APIs or workflows
- Fixing inaccuracies or outdated information
- Improving clarity or completeness

### 📋 **Documentation Checklist**
- [ ] Update relevant existing docs
- [ ] Add examples and code snippets
- [ ] Test all instructions work
- [ ] Keep navigation links current
- [ ] Maintain consistent formatting

### 🎯 **Writing Guidelines**
- **Be specific**: Include exact commands and examples
- **Be current**: Test all instructions on latest code
- **Be helpful**: Anticipate common questions and issues
- **Be organized**: Use clear headings and structure

## Recent Documentation Cleanup

The documentation has been recently reorganized for clarity:

- **✅ Consolidated**: Moved all documentation to `docs/` directory
- **✅ Updated**: All docs reflect current Claude AI + FastAPI architecture
- **✅ Cleaned**: Removed outdated files from old architecture
- **✅ Organized**: Clear navigation and user-focused structure

See [Documentation Cleanup Summary](./DOCUMENTATION_CLEANUP_SUMMARY.md) for details.

---

**📍 Start here**: [Main README](../README.md) → [Development Guide](./DEVELOPMENT.md) → [Architecture Guide](./ARCHITECTURE.md) 
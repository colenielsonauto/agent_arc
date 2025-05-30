# Directory Structure Guide

## 📁 Current Folders Analysis

### ✅ **Keep & Use These**

#### `src/` - **Main Source Code**
```
src/
├── core/           # Business logic (keep)
├── adapters/       # External integrations (keep)
├── api/           # REST/GraphQL endpoints (keep)
├── infrastructure/ # Config, security (keep)
├── agents/        # Multi-agent workflows (future)
└── shared/        # Common utilities (keep)
```
**Purpose**: Your main application code using the new architecture
**Action**: ✅ Keep and actively develop here

#### `tasks/` - **Project Management**
```
tasks/
├── mvp/           # Current development tasks
├── future/        # Future feature planning
└── maintenance/   # Ongoing maintenance tasks
```
**Purpose**: Track development progress and roadmap
**Action**: ✅ Keep, update as you complete tasks

#### `tests/` - **Test Suite**
```
tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
├── e2e/          # End-to-end tests
└── fixtures/     # Test data
```
**Purpose**: Automated testing (critical for quality)
**Action**: ✅ Keep, needs refactoring for new architecture

#### `scripts/` - **Utility Scripts**
```
scripts/
├── test_new_architecture.py  # ✅ New test script
├── test_gmail_auth.py        # 🧹 Needs refactoring
├── watch_gmail.py            # 🧹 Needs refactoring
└── smoke_test.py             # 🧹 Needs refactoring
```
**Purpose**: Development and deployment utilities
**Action**: ✅ Keep, but refactor legacy scripts

#### `docs/` - **Documentation**
```
docs/
├── api/           # API documentation
├── architecture/  # System design docs
└── deployment/    # Deployment guides
```
**Purpose**: Project documentation
**Action**: ✅ Keep, update for new architecture

### 🔧 **DevOps & Deployment**

#### `deploy/` - **Deployment Configurations**
```
deploy/
├── docker/        # Docker configurations
├── kubernetes/    # K8s manifests
├── terraform/     # Infrastructure as Code
└── helm/         # Helm charts
```
**Purpose**: Production deployment
**Action**: ✅ Keep for later, not needed for MVP

#### `.github/` - **GitHub Workflows**
```
.github/
├── workflows/     # CI/CD pipelines
├── ISSUE_TEMPLATE/ # Issue templates
└── PULL_REQUEST_TEMPLATE.md
```
**Purpose**: Automated CI/CD and project management
**Action**: ✅ Keep, very useful for automation

### 🗑️ **Clean Up These**

#### `.venv/` - **Virtual Environment**
```
.venv/            # Python virtual environment files
```
**Purpose**: Isolated Python environment
**Action**: ❌ Should NOT be in git (add to .gitignore)
**Usage**: Created locally with `python -m venv .venv`

#### `functions/` - **Legacy Cloud Functions**
```
functions/        # OLD implementation (already deleted)
```
**Purpose**: Legacy serverless deployment
**Action**: ✅ Already deleted - good!

### 🚀 **Future Features**

#### `ml/` - **Machine Learning Components**
```
ml/
├── prompts/      # Prompt engineering
├── embeddings/   # Vector operations
├── fine_tuning/  # Model customization
└── evaluation/   # Performance metrics
```
**Purpose**: Advanced AI features
**Action**: ✅ Keep for future (Week 4+), not needed for MVP

## 🧹 Cleanup Recommendations

### 1. **Fix .gitignore**
```bash
# Add these to .gitignore
echo ".venv/" >> .gitignore
echo ".env" >> .gitignore
echo ".secrets/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".DS_Store" >> .gitignore
```

### 2. **Remove .venv from Git**
```bash
# If .venv is tracked in git
git rm -r --cached .venv
git commit -m "chore: remove .venv from git tracking"
```

### 3. **Refactor Legacy Scripts**
Priority order:
1. `scripts/test_gmail_auth.py` → Update for new architecture
2. `scripts/watch_gmail.py` → Update for new Gmail adapter
3. `scripts/smoke_test.py` → Update for new API endpoints

## 📚 When to Use Each Folder

### **Daily Development**
```bash
# Work primarily in:
src/                    # Your main code
tasks/mvp/             # Check/update your progress
scripts/               # Run tests and utilities

# Occasionally update:
tests/                 # Add tests as you build
docs/                  # Update documentation
```

### **When Setting Up Environment**
```bash
# Virtual environment (DO NOT commit to git)
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### **When Ready for Production**
```bash
# Use these folders:
deploy/                # Deployment configurations
.github/workflows/     # CI/CD pipelines
ml/                    # Advanced features
```

## 🎯 MVP Focus Areas

**For the next 3 weeks, focus on:**
1. `src/` - Building your application
2. `tasks/mvp/` - Tracking progress
3. `tests/` - Adding tests
4. `scripts/` - Using utilities

**Ignore for now:**
- `deploy/` - Too early for production deployment
- `ml/` - Advanced features for later
- `.github/workflows/` - Set up CI/CD after MVP works

## 🔄 Virtual Environment (.venv) Usage

### **What is .venv?**
- Isolated Python environment for your project
- Contains all your dependencies (FastAPI, etc.)
- Prevents conflicts with other Python projects

### **Daily Usage:**
```bash
# Activate (every time you work on project)
source .venv/bin/activate

# Your prompt will show: (.venv) $

# Install new packages
pip install some-package

# Deactivate when done
deactivate
```

### **Why Not in Git?**
- Contains binary files and OS-specific paths
- Large (hundreds of MB)
- Each developer creates their own
- `pyproject.toml` tracks dependencies instead

## 📋 Recommended Project Structure

**Current MVP needs:**
```
email_router/
├── src/           # ✅ Your main development area
├── tasks/mvp/     # ✅ Track your progress
├── tests/         # ✅ Add tests as you build
├── scripts/       # ✅ Use test_new_architecture.py
├── .env           # ✅ Your local credentials
├── .secrets/      # ✅ OAuth files
└── .venv/         # ✅ Local only (not in git)
```

**Future additions:**
```
├── docs/          # When you need documentation
├── deploy/        # When ready for production
├── ml/            # For advanced AI features
└── .github/       # For automated workflows
```

This structure grows with your project complexity! 
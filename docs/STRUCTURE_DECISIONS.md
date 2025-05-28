# Project Structure Decisions

## 🏗️ **Current Architecture**

```
email_router/
├── src/email_router/           # Core package (business logic)
├── functions/email_router/     # Cloud Function deployment wrapper
├── .secrets/                   # Local development credentials
├── tests/                      # Test suite
├── docs/                       # Documentation
├── scripts/                    # Operational utilities
├── .env.example               # Environment template
└── pyproject.toml             # Project configuration
```

## 🎯 **Why This Structure Works**

### **1. Separation of Concerns**
- **`src/`**: Pure business logic, testable, reusable
- **`functions/`**: Thin deployment wrapper for Cloud Functions
- **`.secrets/`**: Local development credentials (git-ignored)

### **2. Standard Python Practices**
- **src-layout**: Prevents accidental imports during development
- **pyproject.toml**: Modern Python packaging standard
- **pytest configuration**: Proper test discovery and imports

### **3. Cloud Function Best Practices**
- **Minimal deployment package**: Only essential files in `functions/`
- **Path-based imports**: Dynamic import from `src/` via sys.path
- **Environment isolation**: Secrets managed separately

## 🤔 **Alternative Architectures Considered**

### **Option A: Single Directory**
```
email_router/
└── email_router/              # Everything in one place
    ├── main.py               # Cloud Function entry
    ├── core/                 # Business logic
    └── config/               # Configuration
```
**Pros**: Simpler structure  
**Cons**: Harder to test, deployment includes unnecessary files

### **Option B: Full Enterprise Structure**
```
email_router/
├── src/email_router/          # Source code
├── infrastructure/            # Terraform/IaC
├── ci/                        # CI/CD pipelines
├── monitoring/                # Observability configs
└── deployments/               # Multiple environment configs
    ├── dev/
    ├── staging/
    └── prod/
```
**Pros**: Scales to large organizations  
**Cons**: Over-engineered for MVP, maintenance overhead

## ✅ **Our Decision: Balanced Approach**

### **Why We Chose Current Structure:**
1. **Right-sized complexity**: Professional but not over-engineered
2. **Testability**: Clear separation allows proper unit testing
3. **Deployability**: Clean Cloud Function packaging
4. **Maintainability**: Easy to understand and modify
5. **Scalability**: Can evolve to Option B when needed

### **Secrets Management Strategy:**
- **Local Development**: `.secrets/` directory (git-ignored)
- **Production**: Environment variables via Cloud Function configuration
- **Future**: Can migrate to Secret Manager when scale demands it

### **Functions vs Source:**
- **Not duplication**: `functions/` is a thin wrapper
- **Clear responsibility**: Source = logic, Functions = deployment
- **Testable architecture**: Can test business logic independently

## 📚 **Trade-offs Made**

### **Accepted Complexity:**
- Two import paths (acceptable for clear separation)
- Additional directory structure (justified by organization)

### **Rejected Alternatives:**
- **Full enterprise**: Too much overhead for current scale
- **Single directory**: Would compromise testability and deployment clarity
- **External secret management**: Overkill for MVP stage

## 🔄 **Evolution Path**

When the project grows, we can:
1. **Add infrastructure/**: When we need Terraform/multi-environment
2. **Add monitoring/**: When observability requirements grow
3. **External secrets**: When security requirements demand it
4. **Multiple functions**: Current structure already supports this

## 🎯 **Conclusion**

Our current structure represents a **pragmatic balance** between:
- Professional practices ✅
- Development velocity ✅  
- Maintenance simplicity ✅
- Future scalability ✅

It follows Python best practices while remaining appropriate for a Cloud Function MVP. 
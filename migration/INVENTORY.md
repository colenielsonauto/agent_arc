# 📋 MIGRATION INVENTORY - EMAIL ROUTER CORE → MULTI-TENANT SAAS

**Generated:** `date`  
**Objective:** Convert single-client email router into true multi-tenant SaaS

## 🎯 HARD-CODED CLIENT DATA DISCOVERED

### 1. ROUTING RULES (`app/routers/webhooks.py:18-26`)
**Current (Hard-coded):**
```python
ROUTING_RULES = {
    "support": "colenielson.re@gmail.com",
    "billing": "colenielson8@gmail.com", 
    "sales": "colenielson@u.boisestate.edu",
    "technical": "colenielson.re@gmail.com",
    "complaint": "colenielson8@gmail.com",
    "general": "colenielson.re@gmail.com"
}
```
**Target:** `clients/active/{client-id}/routing-rules.yaml`

### 2. RESPONSE TIME CONFIGURATION (`app/utils/email_templates.py:21-27`)
**Current (Hard-coded):**
```python
response_times = {
    "support": "within 4 hours",
    "billing": "within 24 hours", 
    "sales": "within 2 hours",
    "general": "within 24 hours"
}
```
**Target:** `clients/active/{client-id}/sla-config.yaml`

### 3. EMAIL SENDER BRANDING (`app/services/email_sender.py:91`)
**Current (Hard-coded):**
```python
"from": f"AI Email Router <admin@{config.mailgun_domain}>",
```
**Target:** `clients/active/{client-id}/client-config.yaml` → branding section

### 4. CLASSIFICATION PROMPT (`app/services/classifier.py:23-42`)
**Current (Hard-coded):**
```python
prompt = f"""
You are an intelligent email classifier for a business. Analyze this email and classify it:

Categories:
- billing: Payment issues, invoices, account billing
- support: Technical problems, how-to questions, product issues  
- sales: Pricing inquiries, product demos, new business
- general: Everything else
```
**Target:** `clients/active/{client-id}/ai-context/classification-prompt.md`

### 5. CUSTOMER ACKNOWLEDGMENT PROMPTS (`app/services/email_composer.py:21-37`)
**Current (Hard-coded):**
Business-specific acknowledgment generation prompts
**Target:** `clients/active/{client-id}/ai-context/acknowledgment-prompt.md`

### 6. TEAM ANALYSIS PROMPTS (`app/services/email_composer.py:75-95`)
**Current (Hard-coded):**
Business context for team analysis generation
**Target:** `clients/active/{client-id}/ai-context/team-analysis-prompt.md`

### 7. FALLBACK RESPONSES (`app/services/email_composer.py:141-156`)
**Current (Hard-coded):**
```python
fallback_responses = {
    "support": "Thank you for contacting our support team...",
    "billing": "Thank you for your billing inquiry...",
    "sales": "Thank you for your interest in our services...",
    "general": "Thank you for contacting us..."
}
```
**Target:** `clients/active/{client-id}/ai-context/fallback-responses.yaml`

### 8. EMAIL TEMPLATES STYLING (`app/utils/email_templates.py:48-85`)
**Current (Hard-coded):**
- Company branding colors (`#667eea`, `#764ba2`)
- Email signatures ("Support Team")
- Template styling and layout
**Target:** `clients/active/{client-id}/branding/`

## 🏗️ AFFECTED FILES REQUIRING REFACTORING

| File | Issue | Migration Action |
|------|-------|------------------|
| `app/routers/webhooks.py` | Hard-coded routing rules | Replace with `client_manager.get_routing_rules()` |
| `app/services/classifier.py` | Fixed classification prompt | Inject client-specific prompts via `template_engine.py` |
| `app/services/email_composer.py` | Static prompts & fallbacks | Load from client AI context directory |
| `app/services/email_sender.py` | Hard-coded sender branding | Read from client config |
| `app/utils/email_templates.py` | Fixed response times & styling | Load from client SLA & branding config |

## 🎯 NEW ARCHITECTURE MAPPING

### Current Structure:
```
app/
├── services/{classifier.py, email_composer.py, email_sender.py}
├── utils/{config.py, email_templates.py}
├── routers/webhooks.py
└── models/schemas.py
```

### Target Structure:
```
clients/
├── templates/default/
│   ├── client-config.yaml
│   ├── routing-rules.yaml  
│   ├── categories.yaml
│   ├── sla-config.yaml
│   ├── ai-context/{classification,acknowledgment,team-analysis}-prompt.md
│   ├── branding/{colors.yaml, templates/}
│   └── monitoring/{dashboard,alerts}-config.yaml
├── templates/onboarding-checklist.md
└── active/
    ├── client-001-acme-corp/
    └── client-002-startup-xyz/

app/
├── services/
│   ├── client_manager.py          # NEW: Multi-tenant client management
│   ├── dynamic_classifier.py      # REFACTOR: classifier.py
│   ├── template_engine.py         # NEW: AI prompt composition
│   └── routing_engine.py          # NEW: Dynamic routing logic
├── models/
│   ├── client_config.py          # NEW: Pydantic models for YAML
│   └── routing_models.py         # NEW: Routing data models  
├── utils/
│   ├── client_loader.py          # NEW: YAML loading & validation
│   └── domain_resolver.py        # NEW: Domain → client mapping
└── routers/webhooks.py           # REFACTOR: Add client identification
```

## 🚀 MIGRATION PRIORITIES

### Phase 1: Framework (Milestone 2)
- [ ] Create directory structure
- [ ] Build pydantic models for YAML schemas
- [ ] Implement `client_loader.py` and `client_manager.py`

### Phase 2: Services Refactor (Milestone 3)
- [ ] Refactor classifier → dynamic_classifier
- [ ] Create template_engine for prompt composition
- [ ] Update routing logic to use client configs

### Phase 3: Client Identification (Milestone 4)
- [ ] Add domain resolution logic
- [ ] Update webhook handler for multi-tenancy

### Phase 4: Tooling (Milestone 5)
- [ ] CLI onboarding wizard
- [ ] Client migration scripts

## 🧪 TESTING IMPLICATIONS

**Current Tests:** 1 file, basic webhook testing  
**Required Tests:** 
- Client config loading/validation
- Multi-tenant routing logic  
- Domain resolution
- Template engine
- Parameterized tests across client configs

## 💾 DATA EXTRACTION FOR FIRST CLIENT

**Current Single Client (Implicit):**
- Domain: `{config.mailgun_domain}`
- Routing: Cole Nielson's email addresses
- Industry: Unknown  
- Timezone: Unknown
- Business Hours: Unknown

**Action:** Create `client-001-cole-nielson` as migration of current hard-coded values.

---

**Next Step:** Milestone 2 - Scaffold Multi-Tenant Framework 🏗️ 
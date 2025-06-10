# 🚀 CLIENT ONBOARDING CHECKLIST

This checklist guides you through setting up a new client in the multi-tenant email router system.

## 📋 Pre-Onboarding Information Gathering

Before starting the onboarding process, collect the following information from the client:

### Basic Client Information
- [ ] Company name and legal entity name
- [ ] Industry/business sector
- [ ] Primary business timezone
- [ ] Business hours (e.g., "9-17", "24/7")
- [ ] Primary contact person and email
- [ ] Escalation contact (manager/supervisor)

### Email Configuration
- [ ] Primary company domain (e.g., "company.com")
- [ ] Support email address (e.g., "support@company.com")
- [ ] Mailgun domain for sending (e.g., "mg.company.com")
- [ ] List of team member emails for routing
- [ ] Any VIP customer domains

### Branding & Style
- [ ] Company logo URL
- [ ] Primary brand color (hex code)
- [ ] Secondary brand color (hex code)
- [ ] Preferred email signature
- [ ] Company footer text

### Service Level Agreements
- [ ] Response time expectations by category
- [ ] Business hours vs. after-hours handling
- [ ] Escalation preferences
- [ ] Holiday calendar (if applicable)

## 🛠️ Technical Setup Process

### Step 1: Create Client Directory Structure
```bash
# Run the onboarding CLI wizard
python -m scripts.onboard_client --name "Company Name"
```

### Step 2: Configure Client Settings
- [ ] Edit `clients/active/client-xxx-company/client-config.yaml`
- [ ] Edit `clients/active/client-xxx-company/routing-rules.yaml`
- [ ] Edit `clients/active/client-xxx-company/categories.yaml`
- [ ] Edit `clients/active/client-xxx-company/sla-config.yaml`

### Step 3: Customize AI Context
- [ ] Review and customize `ai-context/classification-prompt.md`
- [ ] Review and customize `ai-context/acknowledgment-prompt.md`
- [ ] Review and customize `ai-context/team-analysis-prompt.md`
- [ ] Review and customize `ai-context/fallback-responses.yaml`

### Step 4: Brand Customization
- [ ] Update `branding/colors.yaml` with client colors
- [ ] Test email templates with client branding
- [ ] Verify brand consistency across templates

### Step 5: Testing & Validation
- [ ] Send test email to client's support address
- [ ] Verify classification works correctly
- [ ] Test routing to correct team members
- [ ] Confirm acknowledgment emails look correct
- [ ] Validate response times match SLA

### Step 6: Monitoring Setup
- [ ] Configure monitoring dashboard
- [ ] Set up SLA breach alerts
- [ ] Test escalation workflows
- [ ] Document any custom requirements

## ✅ Post-Onboarding Verification

### Functional Testing
- [ ] Email classification accuracy > 85%
- [ ] Routing to correct team members
- [ ] Acknowledgment emails sent successfully
- [ ] Team analysis emails received
- [ ] Response time tracking working

### Client Communication
- [ ] Send onboarding completion email to client
- [ ] Provide client with:
  - [ ] Support email address to use
  - [ ] Expected response times
  - [ ] Escalation process
  - [ ] Contact information for issues

### Documentation
- [ ] Update client database/CRM
- [ ] Document any custom configurations
- [ ] Add client to monitoring dashboard
- [ ] Schedule follow-up check-in (1 week)

## 🚨 Common Issues & Troubleshooting

### Classification Issues
- **Problem:** Low confidence scores
- **Solution:** Review and refine classification prompt
- **Prevention:** Use client-specific keywords and context

### Routing Problems  
- **Problem:** Emails going to wrong team members
- **Solution:** Double-check routing-rules.yaml email addresses
- **Prevention:** Test with actual email addresses before go-live

### Branding Issues
- **Problem:** Colors or styling don't match client brand
- **Solution:** Update branding/colors.yaml and regenerate templates  
- **Prevention:** Get brand guidelines upfront

### Response Time Issues
- **Problem:** SLA breaches or incorrect expectations
- **Solution:** Review sla-config.yaml timing settings
- **Prevention:** Align expectations during onboarding call

## 📞 Support & Escalation

If you encounter issues during onboarding:

1. **Technical Issues:** Contact development team
2. **Client Questions:** Escalate to account management
3. **Urgent Problems:** Use emergency escalation process

## 📚 Additional Resources

- [Client Configuration Schema Reference](../docs/config-schema.md)
- [AI Prompt Engineering Guide](../docs/ai-prompts.md)
- [Email Template Customization](../docs/email-templates.md)
- [Monitoring & Analytics Setup](../docs/monitoring.md)

---

**Estimated Onboarding Time:** 2-3 hours per client  
**Recommended Team:** 1 technical lead + 1 account manager 
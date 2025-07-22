# CanvasOps Django LTI – Product Requirements Document
**Version:** 2.0 (Django Migration)  
**Status:** In Progress  
**Owner:** ACU Learning Technology Team  
**Created:** January 2025

---

## 🎯 1. Executive Summary

CanvasOps is migrating from React prototype to production-ready Python/Django LTI application for seamless Canvas integration. This eliminates CORS restrictions, provides native Canvas authentication, and leverages existing Python Canvas automation scripts.

### Key Changes from Phase 1
- **LTI 1.3 Integration** for native Canvas embedding
- **Python/Django backend** with existing script compatibility
- **Canvas API SDK** for robust API interactions
- **Production deployment** on cloud infrastructure

### Lessons Learned & Best Practices
- Use the latest compatible version of pylti1p3 (2.0.0 as of this project); older versions may not install or import correctly.
- Always generate and reference the correct private/public keys. Ensure file names and paths match your config.
- All LTI config URLs (login, launch, JWK) must match the deployed app's HTTPS URL exactly.
- Double-check Client ID and Deployment ID in both lti_config.json and Canvas Developer Key.
- For local testing, use ngrok or Railway HTTPS to avoid SameSite cookie and CORS issues.
- **NEW:** Always confirm which Django template is rendered for each route before making UI changes. If multiple templates exist for similar pages, update all or unify them. Commit, push, and redeploy after template changes. Use Tailwind CSS CDN for rapid UI prototyping. Hard refresh and clear cache after deployment. If changes don't show, check for template caching or path mismatches.

### UI/UX Lessons Learned (Landing Page)
- Find & Replace tool is now implemented, styled with ACU branding, and live in Canvas.
- Human-centered language and feedback are used throughout the UI.
- Tailwind CSS is loaded via CDN for rapid prototyping and modern UI.
- Commit, push, and redeploy after template changes to ensure updates are visible.
- Hard refresh the browser and clear any CDN or platform cache after deployment to see changes.
- For AI agents: Always check both the view logic and template directory structure before making UI edits. Document which template is mapped to which route.
- For human developers: If changes don't show up, check for template caching, static file issues, or mismatched template paths.

---

## 🏗️ 2. Technical Architecture

### Core Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Django 4.2+ | Web framework, API handling |
| **Frontend** | Django Templates + Alpine.js | Server-side rendering with reactive components |
| **LTI** | pylti1p3 | Canvas LTI 1.3 authentication |
| **Canvas API** | canvasapi Python SDK | Canvas API interactions |
| **Database** | PostgreSQL | User sessions, script metadata, execution logs |
| **Task Queue** | Celery + Redis | Background script execution |
| **Deployment** | Docker + Cloud Platform | Containerized deployment |

### LTI Integration Flow
```
Canvas Course → LTI Launch → Django App → Tool Selection → Script Execution → Results Display
```

---

## 👥 3. User Roles & Authentication

| Role | Authentication | Permissions |
|------|----------------|-------------|
| **Course Instructor** | Canvas LTI SSO | Run tools on own courses |
| **Learning Technologist** | Canvas LTI SSO + Role Check | Run tools on any course, submit scripts |
| **Learning Designer** | Canvas LTI SSO + Role Check | Run tools on assigned courses, submit scripts |
| **Platform Admin** | Canvas LTI SSO + Admin Role | All permissions, script approval, user management |

---

## 🛠️ 4. Feature Requirements

### 4.1 LTI Integration
- **LTI 1.3 Compliance** with Canvas security standards
- **Deep Linking** for course-specific tool access
- **Grade Passback** for audit trail (optional)
- **Context-aware** tool availability based on course permissions

### 4.2 Tool Execution Engine
- **Background Processing** via Celery for long-running scripts
- **Real-time Progress** updates via WebSockets
- **Script Sandboxing** for security isolation
- **Resource Limits** to prevent server overload

### 4.3 Enhanced UI/UX
- **Canvas Design System** styling for native look
- **Responsive Design** for mobile Canvas app
- **Progress Indicators** for script execution
- **Download Reports** in Excel/CSV format

### 4.4 Script Management
- **Version Control** for script updates
- **Rollback Capability** for destructive operations
- **Execution History** with detailed logs
- **Performance Metrics** and usage analytics

---

## 🔧 5. Core Tools (Migration Priority)

### Phase 1 Tools (Immediate)
1. **Find & Replace URLs** *(existing Python script)*
2. **Link Checker** *(new implementation)*
3. **Due Date Audit** *(new implementation)*

### Phase 2 Tools (Next Sprint)
4. **Navigation Cleaner**
5. **Orphaned Pages Finder**
6. **Grade Export Formatter**

### Phase 3 Tools (Future)
7. **Content Migration Helper**
8. **Accessibility Checker**
9. **Course Analytics Dashboard**

---

## 🔒 6. Security & Compliance

### LTI Security
- **OAuth 2.0** authentication flow
- **JWT token validation** for all requests
- **Nonce verification** to prevent replay attacks
- **Canvas role-based authorization**

### Data Protection
- **No persistent storage** of Canvas API tokens
- **Encrypted session data** in database
- **Audit logging** for all destructive operations
- **GDPR compliance** for user data handling

### Script Security
- **Input sanitization** for all user inputs
- **Rate limiting** on Canvas API calls
- **Error handling** with safe fallbacks
- **Sandboxed execution** environment

---

## 📊 7. Database Schema

### Core Models
```python
# User sessions and preferences
class UserSession(models.Model):
    canvas_user_id = models.CharField(max_length=100)
    canvas_roles = models.JSONField()
    preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

# Script definitions and metadata
class Script(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    script_file = models.FileField(upload_to='scripts/')
    metadata = models.JSONField()
    version = models.CharField(max_length=20)
    status = models.CharField(choices=STATUS_CHOICES)
    created_by = models.CharField(max_length=100)

# Execution logs and results
class ExecutionLog(models.Model):
    script = models.ForeignKey(Script, on_delete=CASCADE)
    user_id = models.CharField(max_length=100)
    course_id = models.CharField(max_length=100)
    parameters = models.JSONField()
    results = models.JSONField()
    status = models.CharField(choices=EXECUTION_STATUS)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
```

---

## 🚀 8. Deployment Strategy

### Development Environment
- **Local Django** with ngrok for LTI testing
- **Canvas Developer Account** for LTI app registration
- **Docker Compose** for local dependencies

### Production Environment
- **Cloud Platform** (AWS/Azure/GCP)
- **Kubernetes** or managed container service
- **PostgreSQL** managed database
- **Redis** for caching and task queue
- **CDN** for static assets

### LTI Registration Process
1. **Canvas Developer Key** creation
2. **LTI configuration** JSON setup
3. **Institution approval** workflow
4. **Course-level installation** by instructors

---

## 📈 9. Success Metrics

### User Adoption
- **Active LTI launches** per week
- **Tool execution frequency** by type
- **User retention** across semesters
- **Course adoption rate** within ACU

### Performance Metrics
- **Script execution time** averages
- **API call efficiency** and rate limiting
- **Error rates** and failure analysis
- **System uptime** and availability

### Business Impact
- **Time saved** by Learning Technologists
- **Course quality improvements** (link fixes, content updates)
- **Reduced manual QA** effort
- **Improved student experience** through better course content

---

## 🗓️ 10. Timeline & Milestones

### Sprint 1 (2 weeks) - Foundation
- Django project setup with LTI integration
- Canvas API authentication and basic UI
- Find & Replace tool migration from existing script

### Sprint 2 (2 weeks) - Core Features
- Background task processing with Celery
- Link Checker and Due Date Audit tools
- Excel report generation and download

### Sprint 3 (2 weeks) - Production Ready
- Security hardening and testing
- Deployment pipeline and monitoring
- Canvas LTI app registration and approval

### Sprint 4 (1 week) - Launch
- Production deployment
- User training and documentation
- Initial rollout to pilot courses

---

## 📋 11. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Canvas LTI approval delay** | High | Medium | Start approval process early, maintain React fallback |
| **Script execution timeouts** | Medium | High | Implement proper background processing |
| **Canvas API rate limits** | Medium | Medium | Add intelligent rate limiting and retry logic |
| **User adoption resistance** | Low | Medium | Comprehensive training and gradual rollout |

---

## 🔄 12. Migration from React Prototype

### What We Keep
- **UI/UX design patterns** and user workflows
- **Tool specifications** and input requirements
- **Security model** and validation logic

### What Changes
- **Backend implementation** from JavaScript to Python
- **Authentication** from manual tokens to LTI SSO
- **API calls** from client-side to server-side
- **Deployment** from static site to full application

### Migration Benefits
- **No CORS issues** with server-side API calls
- **Native Canvas integration** with LTI
- **Existing script compatibility** with Python ecosystem
- **Production-grade** security and performance

---

## 📚 13. Documentation Requirements

### Technical Documentation
- **API documentation** for script integration
- **Deployment guide** for system administrators
- **LTI configuration** instructions
- **Development setup** for contributors

### User Documentation
- **Tool user guides** with screenshots
- **Best practices** for each automation script
- **Troubleshooting guide** for common issues
- **Video tutorials** for complex workflows

---

## ✅ 14. Definition of Done

### Phase 1 Complete When:
- [ ] LTI 1.3 integration working in Canvas
- [ ] Find & Replace tool fully functional
- [ ] Background processing implemented
- [ ] Basic security measures in place
- [ ] Deployed to production environment

### Phase 2 Complete When:
- [ ] All core tools implemented and tested
- [ ] Excel report generation working
- [ ] User role-based permissions enforced
- [ ] Performance monitoring in place
- [ ] Documentation complete

---

## 📝 15. Lessons Learned & Best Practices

### LTI & Canvas Integration
- Use the latest compatible version of pylti1p3 (2.0.0 as of this project); older versions may not install or import correctly.
- Always generate and reference the correct private/public keys. Ensure file names and paths match your config.
- All LTI config URLs (login, launch, JWK) must match the deployed app's HTTPS URL exactly.
- Double-check Client ID and Deployment ID in both lti_config.json and Canvas Developer Key.
- For local testing, use ngrok or Railway HTTPS to avoid SameSite cookie and CORS issues.

### Django & Hosting
- Store all secrets and config in Railway environment variables, not in code.
- Be aware of Railway free tier limitations (sleep after inactivity, quotas).
- Enable debug logging for pylti1p3 in Django settings for troubleshooting.

### General Development
- Document every error and fix; most LTI issues are config-related and cryptic.
- Test each step (key generation, config, launch) in isolation before combining.
- Sometimes Canvas caches Developer Key/app config—clear cache or re-add the app if changes don't show.

### Best Practices for Future LTI Tools
- Start with a working LTI 1.3 launch before building tool features.
- Automate key generation and config file creation where possible.
- Keep a checklist for Canvas Developer Key, LTI config, and environment variables.
- Use Railway or similar for quick HTTPS deployment/testing.
- Plan for free tier limitations in both dev and pilot phases.

### UI/UX Lessons Learned (Landing Page)
- Always confirm which Django template is being rendered for each route before making UI changes. Use codebase search or view logic to verify.
- If multiple apps (e.g., 'tools' and 'lti') have similarly named templates, update all relevant files or unify them to avoid confusion.
- After updating templates, always commit, push, and redeploy before checking production.
- Use Tailwind CSS via CDN for rapid prototyping and modern UI, but ensure the CDN link is present in the deployed template.
- Hard refresh the browser and clear any CDN or platform cache after deployment to see changes.
- For AI agents: Always check both the view logic and template directory structure before making UI edits. Document which template is mapped to which route.
- For human developers: If changes don't show up, check for template caching, static file issues, or mismatched template paths.

### 2025 Update: First-Time Developer Checklist & Troubleshooting

**Environment Variables:**
- Always set `DATABASE_URL` using actual values, not placeholders. Example:
  `postgres://myuser:mypassword@myhost:5432/mydatabase`
- Do not use `postgres://PGUSER:PGPASSWORD@PGHOST:PGPORT/PGDATABASE` (these are placeholders, not real values).
- Ensure all required secrets (e.g., `SECRET_KEY`, `ENCRYPTION_KEY`, `REDIS_URL`, Canvas LTI keys) are present in your deployment environment.

**Django Middleware Order:**
- `SessionMiddleware` must come **before** any middleware that accesses `request.session` (e.g., `LTIEmbeddingMiddleware`).
- If you see `'WSGIRequest' object has no attribute 'session'`, check your `MIDDLEWARE` order in `settings.py`.

**Template Troubleshooting:**
- If you have multiple apps with templates of the same name, Django may render the wrong one. Remove duplicates or use app-specific template paths.
- If template changes don't show up, check for browser cache, CDN cache, or template path mismatches.

**Deployment Tips:**
- After changing environment variables or settings, always redeploy your app.
- Use Railway logs to debug 500 errors—most are due to misconfigured environment variables or database issues.
- If you see a database connection error, double-check your `DATABASE_URL` and database credentials.

**LTI Launch Debugging:**
- If the LTI tool launches but shows a blank or error page, check for session/cookie issues and ensure your app is served over HTTPS.
- Use the `/tools/tool_selection/` endpoint as a basic health check for LTI launches.

**General Advice:**
- Document every error and its fix for future developers.
- Keep a copy of this checklist in your repo or onboarding docs.
- Test each step (key generation, config, launch) in isolation before combining.

*Following this checklist will help future developers get CanvasOps LTI running smoothly on the first attempt!*

---

## Security and LTI Cookie/Iframe Fixes (2024)
- Private key removed from git history and .gitignore updated to exclude all key files.
- Django settings updated for secure cookies and iframe compatibility (SESSION_COOKIE_SAMESITE=None, X_FRAME_OPTIONS=ALLOWALL, etc.).
- LTIEmbeddingMiddleware and LTISessionMiddleware added for robust LTI session and iframe handling.
- ENCRYPTION_KEY environment variable added for secure key management.
- Production-ready LTI models implemented with encryption, audit logging, and security tracking.
- LTISecurityManager class added for nonce validation, state validation, and input sanitization.
- LTIComplianceManager and LTIAdvantageServices implemented for full LTI 1.3 compliance validation.
- Cookie compatibility test template created for iframe debugging and troubleshooting.
- Security dependencies added (cryptography, django-ratelimit, sentry-sdk) for production hardening.

*This PRD serves as the foundation for migrating CanvasOps to a production-ready Python/Django LTI application with seamless Canvas integration.*

---

## Lessons Learned (LTI/Canvas Integration)

- **Issuer Mismatch:** Ensure the `iss` (issuer) in Canvas matches exactly in your Django `LTI_CONFIG` and `lti_config.json`.
- **Redirect URI:** The `redirect_uri` sent by your tool must match the Canvas Developer Key exactly, including trailing slashes and protocol (`https`).
- **Client ID Consistency:** The `client_id` in Django and Canvas must match. Use environment variables to avoid hardcoding.
- **Key Files:** Private and public keys must be in the correct format and location. Decode base64 keys if needed.
- **CSRF Trusted Origins:** Add your deployed domain and all Canvas domains to `CSRF_TRUSTED_ORIGINS` in Django settings.
- **Session & Cookies:** Set `SESSION_COOKIE_SAMESITE = 'None'` and `SESSION_COOKIE_SECURE = True` for LTI in iframes.
- **target_link_uri:** Your OIDC login view must use the `target_link_uri` from the request if present.
- **Testing:** Always test LTI launch in Canvas Beta before production.
- **Environment Variables:** Set all required env vars (`CANVAS_CLIENT_ID`, secrets, etc.) in your deployment environment.
- **Key Rotation:** Document how to update/rotate keys and update Canvas Developer Key if needed.

## Deployment Checklist (One-Attempt Success)

1. Set up Django project and install dependencies
2. Configure LTI settings in Django (`settings.py` and `lti_config.json`)
3. Generate and place private/public key files
4. Set all required environment variables
5. Register LTI tool in Canvas Developer Keys
   - Use exact URLs for Redirect, OIDC, JWK, etc.
6. Add all domains to CSRF trusted origins
7. Deploy to production
8. Test LTI launch from Canvas (Beta and/or Prod)
9. Check logs for errors and verify session data
10. Document any new issues or fixes
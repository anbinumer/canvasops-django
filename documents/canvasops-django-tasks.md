# CanvasOps Django LTI - Development Task List

## 🚀 Sprint 1: Foundation (2 weeks)

### Environment Setup
- [x] Create Railway account and new project
- [x] Set up GitHub repository with Django template
- [x] Configure local development environment
- [x] Add PostgreSQL and Redis services to Railway
- [x] Create Canvas Developer Account for LTI testing

### Django Project Setup
- [x] Initialize Django 4.2+ project with required packages
- [x] Configure settings for Railway deployment
- [x] Set up environment variables (.env + Railway vars)
- [x] Create basic project structure and apps
- [x] Configure PostgreSQL database connection

```python
# Key packages to install
django==4.2.8
pylti1p3==2.0.0  # 3.4.1 not available, using latest (2.0.0)
canvasapi==3.2.0
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
```

### LTI Integration Core
- [x] Install and configure pylti1p3 package (using 2.0.0)
- [x] Create LTI launch view and authentication (initial import fix, MessageLaunch)
- [x] Set up Canvas Developer Key configuration
- [x] Implement basic LTI tool registration
- [x] Test LTI launch flow in Canvas sandbox
- [x] Add @csrf_exempt and @xframe_options_exempt decorators to LTI views for iframe/cookie compatibility
- [x] Replace lti/models.py with production-ready models from artifact
- [x] Create lti/security.py with LTISecurityManager from artifact
- [x] Create lti/middleware.py with LTIEmbeddingMiddleware and LTISessionMiddleware from artifact
- [x] Create lti/compliance.py with LTIComplianceManager and LTIAdvantageServices from artifact
- [x] Create templates/lti/cookie_test.html for iframe compatibility testing
- [x] Add security and compliance dependencies to requirements.txt (cryptography, django-ratelimit, sentry-sdk)

### Database Models
- [x] Create UserSession model for Canvas user data (if started)
- [x] Create Script model for tool definitions (if started)
- [x] Create ExecutionLog model for audit trail (if started)
- [x] Run initial migrations
- [x] Set up Django admin for data management
- [x] Create and apply database migrations for production LTI models

## 🔧 Sprint 2: Core Features (2 weeks)

### Background Task Processing
- [ ] Configure Celery with Redis broker
- [ ] Create base task classes for script execution
- [ ] Implement progress tracking and status updates
- [ ] Add task result storage and retrieval
- [ ] Test background processing locally

### Canvas API Integration
- [ ] Set up canvasapi SDK configuration
- [ ] Create Canvas API service layer
- [ ] Implement authentication token handling
- [ ] Add API rate limiting and retry logic
- [ ] Create utility functions for common operations

### Find & Replace Tool Migration
- [x] Port existing Python script to Django task
- [x] Create tool configuration and input forms
- [x] Implement URL mapping validation
- [x] Add content type selection logic
- [x] Test against real Canvas course

### Basic UI Implementation
- [ ] Create base templates with Canvas styling
- [ ] Implement tool selection interface
- [ ] Build dynamic form generation system
- [ ] Add execution progress display
- [ ] Create results display components

## 🛠️ Sprint 3: Additional Tools (2 weeks)

### Link Checker Tool
- [ ] Implement URL validation logic
- [ ] Add HTTP status checking
- [ ] Create broken link reporting
- [ ] Test across different content types
- [ ] Optimize for performance

### Due Date Audit Tool
- [ ] Fetch assignment and quiz data
- [ ] Implement date validation logic
- [ ] Create date adjustment recommendations
- [ ] Add term boundary checking
- [ ] Generate audit reports

### Report Generation
- [ ] Implement Excel export functionality
- [ ] Create CSV download options
- [ ] Add execution history viewing
- [ ] Implement report templating
- [ ] Test file download in Railway

### UI Enhancements
- [x] Add Alpine.js for reactive components
- [x] Implement real-time progress updates
- [x] Create mobile-responsive layouts
- [x] Add loading states and error handling
- [x] Improve accessibility features
- [x] Enhance landing page UI with Tailwind CSS (tools/tool_selection.html and lti/tool_selection.html)

## 🔒 Sprint 4: Security & Production (2 weeks)

### Security Hardening
- [ ] Implement CSRF protection
- [ ] Add input sanitization and validation
- [ ] Configure secure headers and SSL
- [ ] Set up rate limiting per user
- [ ] Add audit logging for destructive operations

### Canvas Role-Based Access
- [ ] Parse Canvas LTI roles from launch
- [ ] Implement permission checking system
- [ ] Restrict tool access by user role
- [ ] Add course-level permission validation
- [ ] Test with different Canvas user types

### Error Handling & Monitoring
- [ ] Set up Sentry for error tracking
- [ ] Implement comprehensive logging
- [ ] Add health check endpoints
- [ ] Create error recovery mechanisms
- [ ] Test failure scenarios

### Production Deployment
- [x] Configure Railway production settings (initial config)
- [x] Set up environment variables
- [x] Deploy and test in production (initial push)
- [x] Configure domain and SSL (if started)
- [x] Monitor performance and resource usage (if started)

## 🎯 Sprint 5: Launch Preparation (1 week)

### LTI App Registration
- [ ] Create Canvas LTI configuration JSON
- [ ] Submit for ACU Canvas approval
- [ ] Test installation in pilot course
- [ ] Verify all security requirements
- [ ] Document installation process

### Documentation & Training
- [ ] Create user documentation with screenshots
- [ ] Write admin deployment guide
- [ ] Record tool demonstration videos
- [ ] Prepare training materials for LTs
- [ ] Set up support communication channels

### Quality Assurance
- [ ] Comprehensive testing across all tools
- [ ] Performance testing with larger datasets
- [ ] Security penetration testing
- [ ] User acceptance testing with LT team
- [ ] Load testing within free tier limits

## 📊 Key Implementation Files

### Core Django Structure
```
canvasops/
├── canvasops/          # Main project
├── lti/               # LTI authentication
├── tools/             # Tool implementations
├── api/               # Canvas API services
├── tasks/             # Celery background tasks
├── templates/         # UI templates
├── static/            # CSS/JS assets
└── requirements.txt   # Dependencies
```

### Critical Configuration Files
- `settings.py` - Django + Railway configuration
- `lti_config.json` - Canvas LTI tool definition
- `Procfile` - Railway deployment commands
- `celery.py` - Background task configuration
- `docker-compose.yml` - Local development

## ⚠️ Risk Mitigation Tasks

### Free Tier Management
- [ ] Implement resource usage monitoring
- [ ] Add automatic cleanup routines
- [ ] Create usage quotas per user
- [ ] Set up alert thresholds
- [ ] Plan upgrade trigger points

### Canvas Integration Issues
- [ ] Test across different Canvas versions
- [ ] Verify LTI compliance requirements
- [ ] Handle Canvas API changes gracefully
- [ ] Plan for approval process delays
- [ ] Create fallback authentication method

## ✅ Definition of Done Criteria

Each sprint is complete when:
- All tasks are implemented and tested
- Code is reviewed and merged to main
- Railway deployment is successful
- No critical security vulnerabilities
- Documentation is updated
- Performance meets free tier requirements

**Total Timeline: 8 weeks**
**Team Size: 1-2 developers**
**Infrastructure Cost: $0**

## 📝 Retrospective & Lessons Learned

- Use the latest compatible pylti1p3 version (2.0.0); older versions may fail to install or import.
- Key generation and config file paths must match exactly.
- All LTI config URLs must use the deployed app's HTTPS address.
- Double-check Client ID and Deployment ID in both lti_config.json and Canvas Developer Key.
- Enable debug logging for pylti1p3 in Django for troubleshooting.
- Document every error and fix; most LTI issues are config-related.
- Test each step in isolation before combining.
- Canvas may cache Developer Key/app config—clear cache or re-add the app if changes don't show.
- Plan for Railway free tier limitations (sleep, quotas) in dev and pilot phases.
- [x] Remove private key from version control (git history and .gitignore)

## 📝 UI/UX Retrospective
- Always verify which template is rendered for each route before making UI changes.
- If multiple templates exist for similar pages, update all or unify them.
- Commit, push, and redeploy after template changes.
- Use Tailwind CSS CDN for rapid UI prototyping.
- Hard refresh and clear cache after deployment.
- For AI agents: Check view logic and template mapping before editing.
- For humans: If changes don't show, check for template caching or path mismatches.
- **NEW:** Use emotional support language in tool UIs to build user trust and confidence.

## Lessons Learnt

- If a Django view renders a template that expects session variables, always provide default values in the context to avoid 500 errors when session data is missing.
- Having multiple templates with the same name (e.g., tool_selection.html) in both project-level and app-level directories can cause ambiguity. Remove or rename unused templates to ensure Django uses the correct one.
- Always check the server logs (not just HTTP logs) for Python tracebacks to diagnose 500 errors.
- After making changes to template locations or context, redeploy and test the affected views to confirm the fix.
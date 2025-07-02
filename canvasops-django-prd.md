# CanvasOps Django LTI – Product Requirements Document
**Version:** 2.0 (Django Migration)  
**Status:** Planning Phase  
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

*This PRD serves as the foundation for migrating CanvasOps to a production-ready Python/Django LTI application with seamless Canvas integration.*
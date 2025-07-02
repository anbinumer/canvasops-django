# CanvasOps Free Hosting & Infrastructure Plan

## 🆓 Zero-Cost Infrastructure Stack

### Core Hosting (Free Tiers)
| Service | Provider | Free Limits | Purpose |
|---------|----------|-------------|---------|
| **Web App** | Railway.app | 500 hours/month | Django app hosting |
| **Database** | Railway PostgreSQL | 1GB storage | User data, logs |
| **Background Tasks** | Railway Redis | 25MB memory | Celery task queue |
| **File Storage** | Cloudinary | 25GB storage, 25GB bandwidth | Script files, reports |
| **Domain** | Railway subdomain | Unlimited | `canvasops.up.railway.app` |

### Alternative Free Options
- **Render.com**: 750 hours/month web service + PostgreSQL
- **Fly.io**: 2,340 hours/month + 3GB storage
- **PythonAnywhere**: Limited but stable Django hosting

## 📋 Infrastructure Requirements

### Minimum Specs Needed
```
CPU: 0.5 vCPU (sufficient for Django + Celery)
RAM: 512MB (basic operations, background tasks)
Storage: 2GB (Django app + user uploads)
Database: 1GB PostgreSQL (metadata, logs)
Redis: 25MB (task queue, sessions)
```

### Free Tier Monitoring
- **Railway Metrics**: Built-in monitoring
- **Sentry.io**: Error tracking (5K errors/month free)
- **LogRocket**: Session recording (1K sessions/month)

## 🔧 Setup Costs: $0

### Required Accounts (All Free)
1. **Railway.app** - Primary hosting
2. **Cloudinary** - File storage
3. **GitHub** - Code repository
4. **Canvas Developer Account** - LTI testing

### Optional Free Services
- **Sentry** - Error monitoring
- **PostHog** - Analytics
- **Mailgun** - Email notifications (100 emails/day)

## ⚠️ Free Tier Limitations

### Railway.app Constraints
- **Sleep after inactivity** (30 minutes idle)
- **500 execution hours/month** (~16 hours/day)
- **No custom domain** (only subdomain)
- **Shared resources** (slower performance)

### Scaling Considerations
- **Concurrent users**: ~10-20 max
- **Script execution**: Sequential only
- **File uploads**: 25GB total limit
- **Database**: 1GB storage cap

## 🚀 Deployment Strategy

### Phase 1: Free Tier Deployment
```bash
# Railway deployment
railway login
railway init
railway add postgresql redis
railway deploy
```

### Phase 2: Performance Optimization
- **Efficient database queries** to minimize resource usage
- **File cleanup routines** to stay under storage limits
- **Caching strategies** to reduce API calls

## 💰 Cost Upgrade Path

### When Free Limits Hit
| Resource | Free Limit | Paid Upgrade | Monthly Cost |
|----------|------------|--------------|--------------|
| **Compute** | 500 hours | Unlimited | $5/month |
| **Database** | 1GB | 8GB | $5/month |
| **Storage** | 25GB | 100GB | $9/month |

### Break-Even Analysis
- **Free tier sufficient** for: 1-2 Learning Technologists, <20 courses/month
- **Paid upgrade needed** for: Full ACU deployment, >50 courses/month

## 🔒 Security on Free Tier

### Included Security Features
- **HTTPS** via Railway (automatic SSL)
- **Environment variables** for secrets
- **Database encryption** at rest
- **Network isolation** between services

### Additional Free Security
- **Cloudflare** proxy (free tier)
- **GitHub security scanning** (free for public repos)
- **OWASP dependency check** (free CI/CD)

## 📊 Free Monitoring Stack

### Performance Tracking
```python
# Django settings for free monitoring
INSTALLED_APPS += [
    'django.contrib.admin',  # Built-in admin
    'debug_toolbar',        # Development debugging
]

# Free error tracking
import sentry_sdk
sentry_sdk.init(dsn="your-free-sentry-dsn")
```

### Usage Analytics
- **Django admin** for user activity
- **PostgreSQL logs** for performance
- **Railway metrics** for resource usage

## 🎯 Free Tier Success Strategy

### Optimize for Limits
1. **Efficient code** to minimize CPU usage
2. **Smart caching** to reduce database hits
3. **Cleanup routines** for file storage
4. **Rate limiting** to prevent abuse

### User Management
- **Canvas LTI roles** for access control
- **Usage quotas** per user/course
- **Scheduled maintenance** during low usage

## 🚨 Risk Mitigation

### Free Tier Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Service sleep** | User frustration | Keep-alive pings, user education |
| **Storage limits** | Upload failures | Auto-cleanup, file size limits |
| **Compute limits** | Execution failures | Queue management, user quotas |

### Backup Plans
- **GitHub repository** as code backup
- **Database exports** via Railway CLI
- **Migration scripts** for provider switching

## ✅ Implementation Checklist

### Setup Phase (Week 1)
- [ ] Railway account and project setup
- [ ] PostgreSQL and Redis provisioning
- [ ] GitHub repository creation
- [ ] Basic Django app deployment

### Configuration Phase (Week 2)
- [ ] Environment variables configuration
- [ ] Database migrations
- [ ] Cloudinary file storage setup
- [ ] Canvas LTI app registration

### Testing Phase (Week 3)
- [ ] Local development environment
- [ ] Production deployment testing
- [ ] LTI integration verification
- [ ] Performance monitoring setup

**Total Infrastructure Cost: $0/month**
**Setup Time: ~3 weeks**
**Maintenance: Minimal with automated deployments**
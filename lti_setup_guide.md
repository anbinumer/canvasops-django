# CanvasOps LTI 1.3 Setup Guide

## 🔄 What to Update When Changing Canvas Instance or Keys

Whenever you switch to a new Canvas instance (e.g., from beta to test or production), or if you generate new keys or get a new Client ID/Deployment ID, update **all** of the following:

- **lti_config.json**
  - Update the Canvas instance URL, `client_id`, and `deployment_ids`.
- **Railway (or deployment) environment variables**
  - `CANVAS_CLIENT_ID`
  - `CANVAS_DEPLOYMENT_ID`
  - `CANVAS_INSTANCE_URL` (if used)
- **.env file** (for local development, if used)
  - Update the same variables as above.
- **lti_setup_guide.md** (this file)
  - Update any references to the current instance, Client ID, or Deployment ID for future reference.
- **README.md or internal docs**
  - Update any quickstart/setup instructions with the new values.
- **CI/CD or deployment scripts**
  - If you have scripts that set these variables, update them as well.

> **After updating, always redeploy your app and test the LTI launch in the new Canvas instance.**

---

## 🚦 Which Setup Path Should I Follow?

| Scenario                | Steps to Follow                |
|-------------------------|-------------------------------|
| First-time setup        | Steps 1 → 7 (all steps)       |
| Reinstall after reset   | Steps 4 → 7 (skip 1–3)        |

- **First-time setup:** You need to generate keys, configure environment, and set up everything from scratch.
- **Reinstall (e.g., Canvas Beta reset):** Your keys and config are already set—just re-add the Developer Key and reinstall the app in Canvas.

---

## Overview
This guide walks through setting up full LTI 1.3 integration for CanvasOps with Canvas LMS.

## Prerequisites
- Railway deployment running
- PostgreSQL and Redis configured
- Admin access to Canvas instance

## Step 1: Generate RSA Keys

_Required for: **First-time setup only**_

First, generate the RSA key pair needed for LTI 1.3:

```bash
# Run locally or on Railway
python manage.py generate_lti_keys
```

This creates:
- `private.key` - Keep this secret!
- `public.key` - Used for verification
- `public.jwk` - JSON Web Key format for Canvas

## Step 2: Update Environment Variables

_Required for: **First-time setup only**_

Add these to your Railway environment:

```env
# Canvas OAuth (from Developer Key)
CANVAS_CLIENT_ID=YOUR_CLIENT_ID_HERE
CANVAS_DEPLOYMENT_ID=YOUR_DEPLOYMENT_ID_HERE

# Your Canvas instance URL (update this to your actual Canvas URL)
CANVAS_INSTANCE_URL=https://aculeo.test.instructure.com
```

> **Note:** You will get the Client ID after creating the Developer Key (Step 4) and the Deployment ID after installing the LTI tool in a course (Step 5). You may need to return to this step to update these values.

## Step 3: Update LTI Configuration

_Required for: **First-time setup only**_

Update your `lti_config.json` with your Canvas details:

```json
{
    "https://aculeo.test.instructure.com": {
        "default": true,
        "client_id": "YOUR_CLIENT_ID_HERE",
        "auth_login_url": "https://aculeo.test.instructure.com/api/lti/authorize_redirect",
        "auth_token_url": "https://aculeo.test.instructure.com/login/oauth2/token",
        "auth_audience": null,
        "key_set_url": "https://aculeo.test.instructure.com/api/lti/security/jwks",
        "key_set": null,
        "private_key_file": "private.key",
        "public_key_file": "public.key",
        "deployment_ids": ["YOUR_DEPLOYMENT_ID_HERE"]
    }
}
```

> **Note:** As above, you may need to return to this step after Steps 4 and 5 to fill in the actual Client ID and Deployment ID.

## Step 4: Create Canvas Developer Key

_Required for: **First-time setup and reinstallation**_

1. In Canvas Admin, go to **Admin → Developer Keys**
2. Click **+ Developer Key → + LTI Key**
3. Configure the key:

### Key Settings:
- **Key Name**: CanvasOps
- **Owner Email**: your-email@acu.edu.au
- **Redirect URIs**: 
  ```
  https://canvasops-django-production.up.railway.app/lti/launch/
  ```

### LTI 1.3 Configuration:
- **Target Link URI**: 
  ```
  https://canvasops-django-production.up.railway.app/lti/launch/
  ```
- **OpenID Connect Initiation Url**:
  ```
  https://canvasops-django-production.up.railway.app/lti/login/
  ```
- **JWK Method**: Public JWK URL
- **Public JWK URL**:
  ```
  https://canvasops-django-production.up.railway.app/lti/jwks/
  ```

### LTI Advantage Services:
Enable all:
- ✅ Can create and view assignment data
- ✅ Can view assignment data  
- ✅ Can view submission data
- ✅ Can create and update submission results
- ✅ Can retrieve user data associated with the context
- ✅ Can update public jwk

### Placements:
Configure Course Navigation:
```json
{
  "text": "CanvasOps",
  "enabled": true,
  "visibility": "admins",
  "icon_url": "https://canvasops-django-production.up.railway.app/static/icon.png",
  "placement": "course_navigation",
  "message_type": "LtiResourceLinkRequest",
  "target_link_uri": "https://canvasops-django-production.up.railway.app/lti/launch/",
  "canvas_icon_class": "icon-lti"
}
```

4. Save the Developer Key
5. Copy the **Client ID** (looks like: 170000000000001)

## Step 5: Install in Canvas Course

_Required for: **First-time setup and reinstallation**_

### As Admin:
1. Go to **Admin → Settings → Apps**
2. Click **+ App**
3. Configuration Type: **By Client ID**
4. Client ID: `YOUR_CLIENT_ID_HERE`
5. Click **Submit**

### As Instructor:
1. Go to **Course Settings → Apps**
2. Find CanvasOps in the list
3. Click **Add** or **Enable**

> **Note:** After installing, you can find the Deployment ID in the Developer Key details. Update your environment variables and config files as needed.

## Step 6: Test the Integration

_Required for: **First-time setup and reinstallation**_

1. Navigate to your Canvas course
2. Look for "CanvasOps" in the course navigation
3. Click it to launch the tool
4. You should see the tool selection page with your Canvas user info

## Step 7: Troubleshooting & Security Checklist

_Required for: **First-time setup and reinstallation (as needed)**_

### Common Issues:

**"Invalid launch" error**
- Check that your client ID matches in Canvas and lti_config.json
- Verify your deployment ID is correct
- Ensure your private/public keys are properly generated

**"OIDC login failed"**
- Verify your redirect URI matches exactly
- Check that cookies are enabled (SameSite=None requires HTTPS)
- Ensure your Railway app is using HTTPS

**Tool doesn't appear in navigation**
- Check placement configuration in Developer Key
- Verify the tool is enabled in the course
- Try clearing Canvas cache

### Debug Mode:
Enable debug logging by adding to settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'pylti1p3': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Security Checklist

- [ ] Private key is not in version control
- [ ] HTTPS is enforced on Railway
- [ ] Session cookies are secure
- [ ] CSRF protection is enabled (except for LTI endpoints)
- [ ] Canvas roles are properly validated
- [ ] API tokens are never stored persistently

---

## Next Steps

1. Implement tool-specific views in `tools/views.py`
2. Add Canvas API integration using `canvasapi` SDK
3. Set up Celery for background processing
4. Create tool execution templates
5. Add logging and monitoring

## Resources

- [Canvas LTI 1.3 Documentation](https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html)
- [PyLTI1.3 Documentation](https://github.com/dmitry-viskov/pylti1.3)
- [IMS LTI 1.3 Specification](http://www.imsglobal.org/spec/lti/v1p3/)

## Lessons Learned & Troubleshooting

### Common Pitfalls
- Using an incompatible pylti1p3 version (use 2.0.0 as of this project)
- Incorrect or mismatched private/public key files or paths
- LTI config URLs not matching deployed app's HTTPS address
- Client ID and Deployment ID mismatches between Canvas and lti_config.json
- Not using HTTPS for all LTI endpoints (causes SameSite/cookie issues)
- Canvas caching Developer Key/app config (clear cache or re-add app)

### Best Practices
- Test LTI launch flow before building tool features
- Store all secrets/config in Railway environment variables
- Enable debug logging for pylti1p3 in Django
- Document every error and fix
- Use Railway/ngrok for quick HTTPS testing
- Keep a checklist for Canvas Developer Key, LTI config, and environment variables

### Troubleshooting Checklist
- Double-check all config values (Client ID, Deployment ID, URLs)
- Ensure keys are generated and referenced correctly
- Use debug logs to trace LTI launch errors
- If tool doesn't appear in Canvas, check placement config and clear cache
- For connection errors, verify Railway app is awake and using HTTPS

---

## Troubleshooting & Error Prevention

### Common LTI/Canvas Errors and Solutions

- **Invalid redirect_uri**
  - **Cause:** The redirect URI sent by your tool does not match the Canvas Developer Key exactly (including trailing slash and protocol).
  - **Fix:** Double-check the Redirect URI in both Canvas and Django. They must match exactly.

- **Issuer not found**
  - **Cause:** The `iss` (issuer) from Canvas is not present in your Django LTI config.
  - **Fix:** Add every Canvas instance you use (beta, prod, test) to your LTI config.

- **Session not persisting / 400 Bad Request**
  - **Cause:** Cookies not set up for cross-site/iframe use, or missing session variables.
  - **Fix:** Set `SESSION_COOKIE_SAMESITE = 'None'` and `SESSION_COOKIE_SECURE = True` in Django settings. Ensure session variables are set after LTI launch.

- **Key file issues**
  - **Cause:** Private/public keys are missing, in the wrong format, or not decoded from base64.
  - **Fix:** Ensure keys are in PEM format and in the correct location. Decode from base64 if needed.

- **CSRF errors**
  - **Cause:** Canvas or your app domain not in `CSRF_TRUSTED_ORIGINS`.
  - **Fix:** Add all relevant domains to `CSRF_TRUSTED_ORIGINS` in Django settings.

- **General Debugging Tips**
  - Check Django logs for error messages.
  - Use browser dev tools to inspect network requests and parameters (especially `redirect_uri` and `iss`).
  - Test in Canvas Beta before production.
  - After any config change, clear browser cache and cookies, and re-authenticate in Canvas.

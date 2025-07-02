from django.db import models

class LTIKey(models.Model):
    issuer = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    key_set_url = models.URLField()
    auth_token_url = models.URLField()
    auth_login_url = models.URLField()
    deployment_id = models.CharField(max_length=255, blank=True)
    private_key = models.TextField()
    
    class Meta:
        unique_together = ('issuer', 'client_id')

class LTISession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    user_id = models.CharField(max_length=255)
    canvas_user_id = models.CharField(max_length=255)
    canvas_course_id = models.CharField(max_length=255, blank=True)
    canvas_roles = models.JSONField(default=list)
    canvas_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
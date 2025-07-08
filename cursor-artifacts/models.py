# lti/models.py - Production-ready models
from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
from cryptography.fernet import Fernet
from django.conf import settings
import json

class TimestampedModel(models.Model):
    """Base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        unique_together = ('line_item', 'user_id')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['submission_timestamp']),
            models.Index(fields=['grading_progress']),
        ]
    
    def __str__(self):
        return f"Grade: {self.score_given}/{self.score_maximum} for {self.user_id}"

class LTIAuditLog(TimestampedModel):
    """Comprehensive audit logging for LTI operations"""
    # Event identification
    event_type = models.CharField(max_length=50, db_index=True, choices=[
        ('launch', 'LTI Launch'),
        ('grade_submit', 'Grade Submission'),
        ('deep_link', 'Deep Linking'),
        ('names_roles', 'Names and Roles Access'),
        ('error', 'Error Event'),
        ('security_violation', 'Security Violation'),
    ])
    
    # Context
    session = models.ForeignKey(LTISession, on_delete=models.SET_NULL, null=True, blank=True)
    user_id = models.CharField(max_length=255, blank=True, db_index=True)
    context_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Event details
    description = models.TextField()
    details = models.JSONField(default=dict)
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['success', 'event_type']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.event_type.upper()} - {status} - {self.created_at}"

class LTISecurityEvent(TimestampedModel):
    """Security-specific events requiring attention"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('nonce_reuse', 'Nonce Reuse Attempt'),
        ('invalid_signature', 'Invalid JWT Signature'),
        ('expired_token', 'Expired Token'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('unauthorized_access', 'Unauthorized Access Attempt'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, db_index=True)
    
    # Context
    user_id = models.CharField(max_length=255, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Event details
    description = models.TextField()
    technical_details = models.JSONField(default=dict)
    
    # Response
    action_taken = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['severity', 'resolved', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.severity.upper()} - {self.event_type} - {self.created_at}"

# Management commands for maintenance
class LTIMaintenanceTask(TimestampedModel):
    """Track maintenance and cleanup tasks"""
    TASK_CHOICES = [
        ('session_cleanup', 'Clean Expired Sessions'),
        ('audit_cleanup', 'Clean Old Audit Logs'),
        ('security_scan', 'Security Scan'),
        ('key_rotation', 'Key Rotation'),
    ]
    
    task_type = models.CharField(max_length=50, choices=TASK_CHOICES)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['created_at']),
        ]

# Migration for adding encryption key setting
# settings.py addition:
# ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())

# Management command: python manage.py cleanup_lti_sessions
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Clean up expired LTI sessions and old audit logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete sessions older than N days'
        )
        parser.add_argument(
            '--audit-days',
            type=int,
            default=90,
            help='Delete audit logs older than N days'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        audit_days = options['audit_days']
        
        # Clean expired sessions
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_sessions = LTISession.objects.filter(
            models.Q(expires_at__lt=timezone.now()) |
            models.Q(last_activity__lt=cutoff_date)
        )
        
        session_count = expired_sessions.count()
        expired_sessions.delete()
        
        # Clean old audit logs
        audit_cutoff = timezone.now() - timedelta(days=audit_days)
        old_logs = LTIAuditLog.objects.filter(created_at__lt=audit_cutoff)
        
        log_count = old_logs.count()
        old_logs.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned {session_count} expired sessions and {log_count} old audit logs'
            )
        ):
        abstract = True

class LTIPlatform(TimestampedModel):
    """LTI Platform (Canvas instance) configuration"""
    name = models.CharField(max_length=255)
    issuer = models.URLField(unique=True, validators=[URLValidator()])
    client_id = models.CharField(max_length=255)
    deployment_ids = models.JSONField(default=list, help_text="List of deployment IDs")
    
    # LTI URLs
    auth_login_url = models.URLField()
    auth_token_url = models.URLField()
    key_set_url = models.URLField()
    
    # Configuration
    private_key_encrypted = models.TextField(help_text="Encrypted private key")
    public_key_jwk = models.JSONField(help_text="Public key in JWK format")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('issuer', 'client_id')
        indexes = [
            models.Index(fields=['issuer', 'client_id']),
            models.Index(fields=['is_active', 'last_used']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.issuer})"
    
    def get_private_key(self):
        """Decrypt and return private key"""
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        return cipher.decrypt(self.private_key_encrypted.encode()).decode()
    
    def set_private_key(self, private_key_pem):
        """Encrypt and store private key"""
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        self.private_key_encrypted = cipher.encrypt(private_key_pem.encode()).decode()

class LTIDeployment(TimestampedModel):
    """Individual LTI deployment within a platform"""
    platform = models.ForeignKey(LTIPlatform, on_delete=models.CASCADE, related_name='deployments')
    deployment_id = models.CharField(max_length=255)
    context_id = models.CharField(max_length=255, blank=True, help_text="Course/context ID")
    context_title = models.CharField(max_length=255, blank=True)
    
    # Permissions
    can_read_gradebook = models.BooleanField(default=False)
    can_manage_gradebook = models.BooleanField(default=False)
    can_access_names_roles = models.BooleanField(default=False)
    
    # Usage tracking
    last_launch = models.DateTimeField(null=True, blank=True)
    total_launches = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('platform', 'deployment_id', 'context_id')
        indexes = [
            models.Index(fields=['deployment_id']),
            models.Index(fields=['context_id']),
            models.Index(fields=['last_launch']),
        ]
    
    def __str__(self):
        return f"Deployment {self.deployment_id} - {self.context_title}"

class LTISession(TimestampedModel):
    """LTI launch session with security tracking"""
    # Session identification
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    launch_id = models.CharField(max_length=255, unique=True)
    
    # Platform and deployment
    platform = models.ForeignKey(LTIPlatform, on_delete=models.CASCADE)
    deployment = models.ForeignKey(LTIDeployment, on_delete=models.CASCADE, null=True, blank=True)
    
    # User information
    user_id = models.CharField(max_length=255, db_index=True)  # Canvas user ID
    canvas_user_id = models.CharField(max_length=255, db_index=True)  # sub claim
    user_roles = models.JSONField(default=list)
    
    # Context information
    context_id = models.CharField(max_length=255, blank=True, db_index=True)
    context_title = models.CharField(max_length=255, blank=True)
    resource_link_id = models.CharField(max_length=255, blank=True)
    
    # Launch data (encrypted)
    launch_data_encrypted = models.TextField(help_text="Encrypted launch data")
    message_type = models.CharField(max_length=50, default='LtiResourceLinkRequest')
    
    # Security tracking
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    nonce_used = models.CharField(max_length=255, db_index=True)
    
    # Session state
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'context_id']),
            models.Index(fields=['is_active', 'expires_at']),
            models.Index(fields=['nonce_used']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"Session {self.session_key} - {self.user_id}"
    
    def get_launch_data(self):
        """Decrypt and return launch data"""
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted_data = self.launch_data_encrypted.encode()
        decrypted_json = cipher.decrypt(encrypted_data).decode()
        return json.loads(decrypted_json)
    
    def set_launch_data(self, launch_data):
        """Encrypt and store launch data"""
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        json_data = json.dumps(launch_data)
        self.launch_data_encrypted = cipher.encrypt(json_data.encode()).decode()
    
    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration"""
        self.expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.save(update_fields=['expires_at', 'last_activity'])

class LTIGradeLineItem(TimestampedModel):
    """Line items created by the LTI tool"""
    session = models.ForeignKey(LTISession, on_delete=models.CASCADE)
    line_item_id = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255)
    score_maximum = models.FloatField()
    resource_link_id = models.CharField(max_length=255, blank=True)
    
    # Canvas specific
    canvas_assignment_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['line_item_id']),
            models.Index(fields=['canvas_assignment_id']),
        ]
    
    def __str__(self):
        return f"Line Item: {self.label} (Max: {self.score_maximum})"

class LTIGradeSubmission(TimestampedModel):
    """Grade submissions made through AGS"""
    line_item = models.ForeignKey(LTIGradeLineItem, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255, db_index=True)
    score_given = models.FloatField()
    score_maximum = models.FloatField()
    comment = models.TextField(blank=True)
    
    # Status tracking
    activity_progress = models.CharField(max_length=20, default='Completed')
    grading_progress = models.CharField(max_length=20, default='FullyGraded')
    submission_timestamp = models.DateTimeField()
    
    # Response tracking
    response_status = models.CharField(max_length=10, blank=True)  # HTTP status
    response_data = models.JSONField(default=dict)
    
    class Meta
# Generated by Django 4.2.23 on 2025-07-08 05:16

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LTIAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('event_type', models.CharField(choices=[('launch', 'LTI Launch'), ('grade_submit', 'Grade Submission'), ('deep_link', 'Deep Linking'), ('names_roles', 'Names and Roles Access'), ('error', 'Error Event'), ('security_violation', 'Security Violation')], db_index=True, max_length=50)),
                ('user_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('context_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('description', models.TextField()),
                ('details', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('request_path', models.CharField(blank=True, max_length=255)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LTIDeployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('deployment_id', models.CharField(max_length=255)),
                ('context_id', models.CharField(blank=True, help_text='Course/context ID', max_length=255)),
                ('context_title', models.CharField(blank=True, max_length=255)),
                ('can_read_gradebook', models.BooleanField(default=False)),
                ('can_manage_gradebook', models.BooleanField(default=False)),
                ('can_access_names_roles', models.BooleanField(default=False)),
                ('last_launch', models.DateTimeField(blank=True, null=True)),
                ('total_launches', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='LTIGradeLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('line_item_id', models.CharField(max_length=255, unique=True)),
                ('label', models.CharField(max_length=255)),
                ('score_maximum', models.FloatField()),
                ('resource_link_id', models.CharField(blank=True, max_length=255)),
                ('canvas_assignment_id', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='LTIGradeSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('user_id', models.CharField(db_index=True, max_length=255)),
                ('score_given', models.FloatField()),
                ('score_maximum', models.FloatField()),
                ('comment', models.TextField(blank=True)),
                ('activity_progress', models.CharField(default='Completed', max_length=20)),
                ('grading_progress', models.CharField(default='FullyGraded', max_length=20)),
                ('submission_timestamp', models.DateTimeField()),
                ('response_status', models.CharField(blank=True, max_length=10)),
                ('response_data', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='LTIMaintenanceTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('task_type', models.CharField(choices=[('session_cleanup', 'Clean Expired Sessions'), ('audit_cleanup', 'Clean Old Audit Logs'), ('security_scan', 'Security Scan'), ('key_rotation', 'Key Rotation')], max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('details', models.JSONField(default=dict)),
                ('error_message', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LTIPlatform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('issuer', models.URLField(unique=True, validators=[django.core.validators.URLValidator()])),
                ('client_id', models.CharField(max_length=255)),
                ('deployment_ids', models.JSONField(default=list, help_text='List of deployment IDs')),
                ('auth_login_url', models.URLField()),
                ('auth_token_url', models.URLField()),
                ('key_set_url', models.URLField()),
                ('private_key_encrypted', models.TextField(help_text='Encrypted private key')),
                ('public_key_jwk', models.JSONField(help_text='Public key in JWK format')),
                ('is_active', models.BooleanField(default=True)),
                ('last_used', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LTISession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('session_key', models.CharField(db_index=True, max_length=40, unique=True)),
                ('launch_id', models.CharField(max_length=255, unique=True)),
                ('user_id', models.CharField(db_index=True, max_length=255)),
                ('canvas_user_id', models.CharField(db_index=True, max_length=255)),
                ('user_roles', models.JSONField(default=list)),
                ('context_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('context_title', models.CharField(blank=True, max_length=255)),
                ('resource_link_id', models.CharField(blank=True, max_length=255)),
                ('launch_data_encrypted', models.TextField(help_text='Encrypted launch data')),
                ('message_type', models.CharField(default='LtiResourceLinkRequest', max_length=50)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('nonce_used', models.CharField(db_index=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField()),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('deployment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lti.ltideployment')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti.ltiplatform')),
            ],
        ),
        migrations.CreateModel(
            name='LTISecurityEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('event_type', models.CharField(choices=[('nonce_reuse', 'Nonce Reuse Attempt'), ('invalid_signature', 'Invalid JWT Signature'), ('expired_token', 'Expired Token'), ('rate_limit_exceeded', 'Rate Limit Exceeded'), ('suspicious_activity', 'Suspicious Activity'), ('unauthorized_access', 'Unauthorized Access Attempt')], db_index=True, max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], db_index=True, max_length=10)),
                ('user_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('description', models.TextField()),
                ('technical_details', models.JSONField(default=dict)),
                ('action_taken', models.TextField(blank=True)),
                ('resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_by', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'indexes': [models.Index(fields=['severity', 'resolved', 'created_at'], name='lti_ltisecu_severit_b0d7fe_idx'), models.Index(fields=['event_type', 'created_at'], name='lti_ltisecu_event_t_098489_idx'), models.Index(fields=['ip_address', 'created_at'], name='lti_ltisecu_ip_addr_6351ec_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='ltiplatform',
            index=models.Index(fields=['issuer', 'client_id'], name='lti_ltiplat_issuer_37f6d1_idx'),
        ),
        migrations.AddIndex(
            model_name='ltiplatform',
            index=models.Index(fields=['is_active', 'last_used'], name='lti_ltiplat_is_acti_7a3995_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='ltiplatform',
            unique_together={('issuer', 'client_id')},
        ),
        migrations.AddIndex(
            model_name='ltimaintenancetask',
            index=models.Index(fields=['task_type', 'status'], name='lti_ltimain_task_ty_96ed57_idx'),
        ),
        migrations.AddIndex(
            model_name='ltimaintenancetask',
            index=models.Index(fields=['created_at'], name='lti_ltimain_created_b3b22f_idx'),
        ),
        migrations.AddField(
            model_name='ltigradesubmission',
            name='line_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti.ltigradelineitem'),
        ),
        migrations.AddField(
            model_name='ltigradelineitem',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti.ltisession'),
        ),
        migrations.AddField(
            model_name='ltideployment',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='lti.ltiplatform'),
        ),
        migrations.AddField(
            model_name='ltiauditlog',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='lti.ltisession'),
        ),
        migrations.AddIndex(
            model_name='ltisession',
            index=models.Index(fields=['session_key'], name='lti_ltisess_session_e80247_idx'),
        ),
        migrations.AddIndex(
            model_name='ltisession',
            index=models.Index(fields=['launch_id'], name='lti_ltisess_launch__3917b6_idx'),
        ),
        migrations.AddIndex(
            model_name='ltisession',
            index=models.Index(fields=['user_id', 'context_id'], name='lti_ltisess_user_id_891586_idx'),
        ),
        migrations.AddIndex(
            model_name='ltisession',
            index=models.Index(fields=['expires_at'], name='lti_ltisess_expires_f17222_idx'),
        ),
        migrations.AddIndex(
            model_name='ltisession',
            index=models.Index(fields=['is_active', 'last_activity'], name='lti_ltisess_is_acti_daad66_idx'),
        ),
        migrations.AddIndex(
            model_name='ltigradesubmission',
            index=models.Index(fields=['user_id'], name='lti_ltigrad_user_id_edcbb3_idx'),
        ),
        migrations.AddIndex(
            model_name='ltigradesubmission',
            index=models.Index(fields=['submission_timestamp'], name='lti_ltigrad_submiss_af76ab_idx'),
        ),
        migrations.AddIndex(
            model_name='ltigradesubmission',
            index=models.Index(fields=['grading_progress'], name='lti_ltigrad_grading_c23c31_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='ltigradesubmission',
            unique_together={('line_item', 'user_id')},
        ),
        migrations.AddIndex(
            model_name='ltigradelineitem',
            index=models.Index(fields=['line_item_id'], name='lti_ltigrad_line_it_a48da0_idx'),
        ),
        migrations.AddIndex(
            model_name='ltigradelineitem',
            index=models.Index(fields=['session'], name='lti_ltigrad_session_2f1f0f_idx'),
        ),
        migrations.AddIndex(
            model_name='ltideployment',
            index=models.Index(fields=['platform', 'deployment_id'], name='lti_ltidepl_platfor_e6da04_idx'),
        ),
        migrations.AddIndex(
            model_name='ltideployment',
            index=models.Index(fields=['context_id'], name='lti_ltidepl_context_22a192_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='ltideployment',
            unique_together={('platform', 'deployment_id', 'context_id')},
        ),
        migrations.AddIndex(
            model_name='ltiauditlog',
            index=models.Index(fields=['event_type', 'created_at'], name='lti_ltiaudi_event_t_76c3ae_idx'),
        ),
        migrations.AddIndex(
            model_name='ltiauditlog',
            index=models.Index(fields=['user_id', 'created_at'], name='lti_ltiaudi_user_id_1571ac_idx'),
        ),
        migrations.AddIndex(
            model_name='ltiauditlog',
            index=models.Index(fields=['success', 'event_type'], name='lti_ltiaudi_success_b45260_idx'),
        ),
        migrations.AddIndex(
            model_name='ltiauditlog',
            index=models.Index(fields=['ip_address', 'created_at'], name='lti_ltiaudi_ip_addr_80a9af_idx'),
        ),
    ]

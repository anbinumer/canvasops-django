#!/usr/bin/env python
"""
Session table migration script
Run this to ensure the session table exists and is properly configured
"""
import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canvasops.settings')
django.setup()

# Clear existing sessions and regenerate table
from django.core.management import call_command

print("🔄 Clearing existing sessions...")
call_command('clearsessions')

print("📊 Creating session table if needed...")
call_command('migrate', 'sessions')

print("✅ Session table ready!") 
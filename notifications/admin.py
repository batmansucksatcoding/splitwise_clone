from django.contrib import admin

# Register your models here.

# ============================================
# notifications/admin.py
# ============================================
from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('recipient', 'sender', 'notification_type')
        }),
        ('Content', {
            'fields': ('title', 'message', 'action_url')
        }),
        ('Related Objects', {
            'fields': ('expense', 'group'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_digest', 'email_digest_frequency', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']

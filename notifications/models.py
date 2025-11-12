# ============================================
# notifications/models.py
# ============================================
from django.db import models
from django.conf import settings  # ✅ use settings.AUTH_USER_MODEL instead of auth.User
from django.utils import timezone
from expenses.models import Expense
from groups.models import Group


class Notification(models.Model):
    """Notification model for user alerts"""
    
    NOTIFICATION_TYPES = [
        ('expense_added', 'Expense Added'),
        ('expense_edited', 'Expense Edited'),
        ('expense_deleted', 'Expense Deleted'),
        ('payment_received', 'Payment Received'),
        ('payment_reminder', 'Payment Reminder'),
        ('group_invite', 'Group Invite'),
        ('member_added', 'Member Added to Group'),
        ('member_removed', 'Member Removed from Group'),
        ('comment_added', 'Comment Added'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ changed
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ changed
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects (optional)
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Action URL (where to redirect when clicked)
    action_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_icon(self):
        """Get icon for notification type"""
        icons = {
            'expense_added': '💸',
            'expense_edited': '✏️',
            'expense_deleted': '🗑️',
            'payment_received': '💰',
            'payment_reminder': '⏰',
            'group_invite': '👥',
            'member_added': '➕',
            'member_removed': '➖',
            'comment_added': '💬',
        }
        return icons.get(self.notification_type, '🔔')


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ✅ changed
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # In-app notifications
    expense_added = models.BooleanField(default=True)
    expense_edited = models.BooleanField(default=True)
    expense_deleted = models.BooleanField(default=True)
    payment_received = models.BooleanField(default=True)
    payment_reminder = models.BooleanField(default=True)
    group_invite = models.BooleanField(default=True)
    member_changes = models.BooleanField(default=True)
    
    # Email notifications
    email_expense_added = models.BooleanField(default=True)
    email_payment_received = models.BooleanField(default=True)
    email_payment_reminder = models.BooleanField(default=True)
    email_group_invite = models.BooleanField(default=True)
    
    # Frequency
    email_digest = models.BooleanField(default=False)
    email_digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='weekly'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user}"

# ============================================
# notifications/services.py
# ============================================
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Notification, NotificationPreference
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from expenses.models import Expense, Group


class NotificationService:
    """Service for creating and sending notifications"""
    
    @staticmethod
    def create_notification(recipient, notification_type, title, message, 
                          sender=None, expense=None, group=None, action_url=''):
        """Create a new notification"""
        
        # Check user preferences
        try:
            prefs = recipient.notification_preferences
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            prefs = NotificationPreference.objects.create(user=recipient)
        
        # Check if this notification type is enabled
        pref_field = notification_type.replace('_', '_')
        if not getattr(prefs, pref_field, True):
            return None
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            expense=expense,
            group=group,
            action_url=action_url
        )
        
        # Send email if enabled
        email_field = f'email_{notification_type}'
        if getattr(prefs, email_field, False):
            NotificationService.send_email_notification(notification)
        
        return notification
    
    @staticmethod
    def notify_expense_added(expense, recipients=None):
        """Notify users when an expense is added"""
        if recipients is None:
            # Get all group members except the creator
            recipients = expense.group.members.exclude(id=expense.paid_by.id)
        
        title = f"New expense in {expense.group.name}"
        message = f"{expense.paid_by.username} added '{expense.description}' (₹{expense.amount})"
        action_url = reverse('expenses:expense_detail', kwargs={'expense_id': expense.id})
        
        for recipient in recipients:
            NotificationService.create_notification(
                recipient=recipient,
                notification_type='expense_added',
                title=title,
                message=message,
                sender=expense.paid_by,
                expense=expense,
                group=expense.group,
                action_url=action_url
            )
    
    @staticmethod
    def notify_expense_edited(expense, editor):
        """Notify users when an expense is edited"""
        recipients = expense.shares.exclude(user=editor).values_list('user', flat=True)
        recipients = User.objects.filter(id__in=recipients)
        
        title = f"Expense updated in {expense.group.name}"
        message = f"{editor.username} edited '{expense.description}'"
        action_url = reverse('expenses:expense_detail', kwargs={'expense_id': expense.id})
        
        for recipient in recipients:
            NotificationService.create_notification(
                recipient=recipient,
                notification_type='expense_edited',
                title=title,
                message=message,
                sender=editor,
                expense=expense,
                group=expense.group,
                action_url=action_url
            )
    
    @staticmethod
    def notify_expense_deleted(expense_data, deleter):
        """Notify users when an expense is deleted"""
        # expense_data should contain: description, group, affected_users
        title = f"Expense deleted in {expense_data['group'].name}"
        message = f"{deleter.username} deleted '{expense_data['description']}'"
        action_url = reverse('expenses:expense_list')
        
        for recipient in expense_data['affected_users']:
            if recipient != deleter:
                NotificationService.create_notification(
                    recipient=recipient,
                    notification_type='expense_deleted',
                    title=title,
                    message=message,
                    sender=deleter,
                    group=expense_data['group'],
                    action_url=action_url
                )
    
    @staticmethod
    def notify_payment_received(payer, payee, amount, group):
        """Notify when a payment is received"""
        title = "Payment received"
        message = f"{payer.username} paid you ₹{amount}"
        action_url = reverse('balances:user_balances')
        
        NotificationService.create_notification(
            recipient=payee,
            notification_type='payment_received',
            title=title,
            message=message,
            sender=payer,
            group=group,
            action_url=action_url
        )
    
    @staticmethod
    def notify_group_invite(inviter, invitee, group):
        """Notify when user is invited to a group"""
        title = f"Group invitation"
        message = f"{inviter.username} invited you to join '{group.name}'"
        action_url = reverse('group_detail', kwargs={'group_id': group.id})
        
        NotificationService.create_notification(
            recipient=invitee,
            notification_type='group_invite',
            title=title,
            message=message,
            sender=inviter,
            group=group,
            action_url=action_url
        )
    
    @staticmethod
    def send_email_notification(notification):
        """Send email notification"""
        try:
            recipient = notification.recipient
            
            # Render email template
            subject = notification.title
            html_message = render_to_string('notifications/email/notification.html', {
                'notification': notification,
                'site_name': 'Splitwise Clone',
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            })
            
            # Plain text version
            plain_message = f"{notification.message}\n\nView details: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}{notification.action_url}"
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't break the flow
            print(f"Error sending email notification: {e}")
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications"""
        return Notification.objects.filter(recipient=user, is_read=False).count()
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )

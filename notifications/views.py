
# ============================================
# notifications/views.py
# ============================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification, NotificationPreference
from .services import NotificationService


@login_required
def notification_list(request):
    """List all notifications for the user"""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Filter by read/unread
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    context = {
        'notifications': notifications[:50],  # Limit to 50 most recent
        'filter_type': filter_type,
        'unread_count': NotificationService.get_unread_count(request.user),
    }
    
    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'unread_count': NotificationService.get_unread_count(request.user)
        })
    
    # Redirect to action URL if available
    if notification.action_url:
        return redirect(notification.action_url)
    return redirect('notifications:notification_list')


@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read"""
    NotificationService.mark_all_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'unread_count': 0})
    
    return redirect('notifications:notification_list')


@login_required
def notification_preferences(request):
    """View and update notification preferences"""
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        prefs.expense_added = request.POST.get('expense_added') == 'on'
        prefs.expense_edited = request.POST.get('expense_edited') == 'on'
        prefs.expense_deleted = request.POST.get('expense_deleted') == 'on'
        prefs.payment_received = request.POST.get('payment_received') == 'on'
        prefs.payment_reminder = request.POST.get('payment_reminder') == 'on'
        prefs.group_invite = request.POST.get('group_invite') == 'on'
        prefs.member_changes = request.POST.get('member_changes') == 'on'
        
        prefs.email_expense_added = request.POST.get('email_expense_added') == 'on'
        prefs.email_payment_received = request.POST.get('email_payment_received') == 'on'
        prefs.email_payment_reminder = request.POST.get('email_payment_reminder') == 'on'
        prefs.email_group_invite = request.POST.get('email_group_invite') == 'on'
        
        prefs.email_digest = request.POST.get('email_digest') == 'on'
        prefs.email_digest_frequency = request.POST.get('email_digest_frequency', 'weekly')
        
        prefs.save()
        
        return redirect('notifications:notification_preferences')
    
    context = {'preferences': prefs}
    return render(request, 'notifications/preferences.html', context)


@login_required
def get_unread_notifications(request):
    """API endpoint to get unread notifications count"""
    unread_count = NotificationService.get_unread_count(request.user)
    recent_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    )[:5]
    
    notifications_data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'icon': n.get_icon(),
            'action_url': n.action_url,
            'created_at': n.created_at.isoformat(),
        }
        for n in recent_notifications
    ]
    
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications_data
    })

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Notification

@login_required
def get_unread_notifications(request):
    """Return unread notification count as JSON (for 🔔 badge)"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required
def mark_all_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:notification_list')

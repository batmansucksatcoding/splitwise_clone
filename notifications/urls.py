# ============================================
# notifications/urls.py
# ============================================
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('preferences/', views.notification_preferences, name='notification_preferences'),
    path('api/unread/', views.get_unread_notifications, name='get_unread'),
    path('', views.notification_list, name='notification_list'),
    path('get_unread/', views.get_unread_notifications, name='get_unread'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]

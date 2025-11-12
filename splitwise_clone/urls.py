from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views_frontend as account_views
from expenses.views_dashboard import dashboard_view
from accounts.views_frontend import index

urlpatterns = [
    # === Admin ===
    path('admin/', admin.site.urls),

    # === Root URL ===
    path('', index, name='index'),

    # === Dashboard ===
    path('dashboard/', dashboard_view, name='dashboard'),

    # === Frontend (User-facing HTML) ===
    path('', include(('accounts.urls_frontend', 'accounts'), namespace='accounts')),  # ✅ your register/login/friends pages
    path('groups/', include('groups.urls')),
    path('', include('core.urls')),

    # === API Endpoints (DRF only) ===
    path('api/accounts/', include('accounts.urls')),    # ✅ keep API separate
    path('api/groups/', include('groups.urls')),
    path('notifications/', include('notifications.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/activity/', include('activity.urls')),
    path('api/advanced/', include('advanced.urls')),
    path('api/balances/', include('balances.urls', namespace='balances')),
    path('users/', include('users.urls')),

    # === Django Auth (optional built-ins like password reset) ===
    path('accounts/', include('django.contrib.auth.urls')),

    # === Other Pages ===
    path('login/', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('terms/', account_views.terms_of_service, name='terms_of_service'),
    path('privacy/', account_views.privacy_policy, name='privacy_policy'),

    # === Social Auth ===
    path('auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

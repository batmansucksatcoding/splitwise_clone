from django.urls import path
from . import views_frontend as views
app_name = 'accounts'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('friends/', views.friends_list_view, name='friends_list'),
    path('friends/add/<int:user_id>/', views.add_friend_view, name='add_friend'),
    path('friends/accept/<int:request_id>/', views.accept_request_view, name='accept_request'),
    path('friends/search/', views.search_friends_view, name='search_friends'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
]

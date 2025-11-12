from django.urls import path
from . import views  # ensure this import is correct

urlpatterns = [
    path('<int:group_id>/members/', views.get_group_members, name='get_group_members'),
    path('', views.group_list, name='group_list'),
    path('create/', views.create_group, name='create_group'),
    path('<int:pk>/', views.group_detail, name='group_detail'),
    path('<int:pk>/edit/', views.edit_group, name='edit_group'),
    path('<int:pk>/delete/', views.delete_group, name='delete_group'),
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
    path('<int:group_id>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
]

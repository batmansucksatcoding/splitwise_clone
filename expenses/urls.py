from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('<int:expense_id>/', views.expense_detail, name='expense_detail'),
    path('<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('balances/', views.my_balances, name='my_balances'),
    path('<int:expense_id>/pdf/', views.expense_pdf, name='expense_pdf'),
    path('api/group/<int:group_id>/members/', views.get_group_members, name='get_group_members'),
]
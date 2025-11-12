from django.urls import path
from . import views

app_name = 'balances'

urlpatterns = [
    path('my-balances/', views.user_balances_view, name='user_balances'),
    path('group/<int:group_id>/', views.group_balances_view, name='group_balances'),
    path('group/<int:group_id>/simplify/', views.simplify_group_debts, name='simplify_debts'),
    path('group/<int:group_id>/simplify-preview/', views.simplification_preview_view, name='simplify_preview'),
    path('group/<int:group_id>/settle/', views.record_settlement, name='record_settlement'),
    path('group/<int:group_id>/settlements/', views.settlements_history_view, name='settlements_history'),
]


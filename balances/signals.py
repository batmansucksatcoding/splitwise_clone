from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from expenses.models import Expense
from .services import BalanceCalculator

@receiver([post_save, post_delete], sender=Expense)
def recalculate_balances_on_expense_change(sender, instance, **kwargs):
    """Automatically recalculate balances when expense is created/updated/deleted"""
    if instance.group:
        BalanceCalculator.recalculate_group_balances(instance.group)
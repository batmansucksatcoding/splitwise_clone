from django.db import models
from django.contrib.auth import get_user_model
from groups.models import Group
from decimal import Decimal

User = get_user_model()

class Balance(models.Model):
    """Tracks balance between two users in a group"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='balances')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts_owed')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts_receiving')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('group', 'from_user', 'to_user')
        indexes = [
            models.Index(fields=['group', 'from_user']),
            models.Index(fields=['group', 'to_user']),
        ]
    
    def __str__(self):
        return f"{self.from_user.username} owes {self.to_user.username} ₹{self.amount} in {self.group.name}"

class Settlement(models.Model):
    """Records payments between users"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlements')
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)
    settled_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='settlements_created')
    
    class Meta:
        ordering = ['-settled_at']
    
    def __str__(self):
        return f"{self.payer.username} paid {self.receiver.username} ₹{self.amount}"
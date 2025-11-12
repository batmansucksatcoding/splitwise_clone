from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from groups.models import Group  

class ExpenseCategory(models.Model):
    """Categories for organizing expenses"""
    CATEGORY_CHOICES = [
        ('food', 'Food & Dining'),
        ('transport', 'Transportation'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
        ('shopping', 'Shopping'),
        ('healthcare', 'Healthcare'),
        ('travel', 'Travel'),
        ('accommodation', 'Accommodation'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#6366f1')  
    
    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']


class Expense(models.Model):
    """Main expense model"""
    SPLIT_TYPE_CHOICES = [
        ('equal', 'Equal Split'),
        ('unequal', 'Unequal Split'),
        ('percentage', 'Percentage Split'),
    ]
    
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='INR')
    
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='expenses_paid'
    )
    
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='expenses',
        null=True,
        blank=True
    )
    
    category = models.ForeignKey(
        'ExpenseCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    
    split_type = models.CharField(
        max_length=20, 
        choices=SPLIT_TYPE_CHOICES,
        default='equal'
    )
    
    date = models.DateField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - ₹{self.amount}"
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date', '-created_at']),
            models.Index(fields=['paid_by']),
            models.Index(fields=['group']),
        ]
    
    def get_total_shares(self):
        """Calculate total of all shares"""
        return sum(share.amount for share in self.shares.all())
    
    def get_share_for_user(self, user):
        """Get the share amount for a specific user"""
        try:
            return self.shares.get(user=user).amount
        except ExpenseShare.DoesNotExist:
            return Decimal('0.00')
    
    def calculate_balances(self):
        """
        Calculate who owes whom for this expense
        Returns: list of {debtor, creditor, amount} dicts
        """
        balances = []
        
        for share in self.shares.all():
            if share.user.id != self.paid_by.id:
                balances.append({
                    'debtor': share.user,
                    'creditor': self.paid_by,
                    'amount': share.amount
                })
        
        return balances


class ExpenseShare(models.Model):
    """Tracks how much each user owes for an expense"""
    expense = models.ForeignKey(
        Expense, 
        on_delete=models.CASCADE, 
        related_name='shares'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE, 
        related_name='expense_shares'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    class Meta:
        unique_together = ('expense', 'user')
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['user', 'expense']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - ₹{self.amount}"

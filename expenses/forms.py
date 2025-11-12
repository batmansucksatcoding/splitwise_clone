from django import forms
from .models import Expense
from groups.models import Group

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'group', 'paid_by', 'split_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expense title'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'paid_by': forms.Select(attrs={'class': 'form-select'}),
            'split_type': forms.Select(attrs={'class': 'form-select'}),
        }

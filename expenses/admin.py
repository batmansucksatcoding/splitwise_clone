from django.contrib import admin
from .models import Expense, ExpenseShare, ExpenseCategory


class ExpenseShareInline(admin.TabularInline):
    model = ExpenseShare
    extra = 1
    readonly_fields = ['amount', 'percentage']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'currency', 'paid_by', 'group', 'split_type', 'date', 'created_at']
    list_filter = ['split_type', 'category', 'date', 'currency']
    search_fields = ['description', 'notes', 'paid_by__username']
    date_hierarchy = 'date'
    inlines = [ExpenseShareInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('description', 'amount', 'currency', 'date')
        }),
        ('Payment & Split', {
            'fields': ('paid_by', 'split_type', 'group', 'category')
        }),
        ('Additional', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'icon', 'color']
    search_fields = ['name']


@admin.register(ExpenseShare)
class ExpenseShareAdmin(admin.ModelAdmin):
    list_display = ['expense', 'user', 'amount', 'percentage']
    list_filter = ['expense__date']
    search_fields = ['expense__description', 'user__username']
    readonly_fields = ['amount', 'percentage']
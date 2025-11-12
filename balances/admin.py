from django.contrib import admin
from .models import Balance, Settlement

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'amount', 'group', 'updated_at')
    list_filter = ('group', 'updated_at')
    search_fields = ('from_user__username', 'to_user__username', 'group__name')
    readonly_fields = ('updated_at',)

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('payer', 'receiver', 'amount', 'group', 'settled_at', 'created_by')
    list_filter = ('group', 'settled_at')
    search_fields = ('payer__username', 'receiver__username', 'group__name')
    readonly_fields = ('settled_at',)
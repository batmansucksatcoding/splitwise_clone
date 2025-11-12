from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
import json
from groups.models import Group
from .models import Balance, Settlement
from .services import BalanceCalculator

User = get_user_model()

@login_required
def user_balances_view(request):
    """Show all balances for the logged-in user"""
    balances = BalanceCalculator.get_user_balances(request.user)
    
    context = {
        'balances': balances,
        'owes': balances['owes'],
        'owed': balances['owed'],
        'total_owes': balances['total_owes'],
        'total_owed': balances['total_owed'],
        'net_balance': balances['net_balance'],
    }
    
    return render(request, 'balances/user_balances.html', context)

@login_required
def group_balances_view(request, group_id):
    from groups.models import Group
    from .services import BalanceCalculator

    group = get_object_or_404(Group, id=group_id)

    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('dashboard')

    matrix_data = BalanceCalculator.get_group_balance_matrix(group)
    user_balance = BalanceCalculator.get_user_balances(request.user, group)
    simplification_preview = BalanceCalculator.get_simplification_preview(group)

    context = {
        "group": group,
        "members": matrix_data["members"],
        "matrix": matrix_data["matrix"],
        "user_balance": user_balance,
        "simplification_preview": simplification_preview,
    }

    return render(request, "balances/group_balances.html", context)


@login_required
@require_http_methods(["POST"])
def record_settlement(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.user not in group.members.all():
        return JsonResponse({'success': False, 'error': 'Not a group member'}, status=403)

    try:
        data = json.loads(request.body)
        payer_id = int(data.get('payer_id'))
        receiver_id = int(data.get('receiver_id'))
        
        if payer_id == receiver_id:
            return JsonResponse({'success': False, 'error': 'Payer and receiver cannot be the same'})
        
        payer = get_object_or_404(User, id=payer_id)
        receiver = get_object_or_404(User, id=receiver_id)
        
        if payer not in group.members.all() or receiver not in group.members.all():
            return JsonResponse({'success': False, 'error': 'Invalid users'})
        
        amount = data.get('amount')
        if amount is None:
            return JsonResponse({'success': False, 'error': 'Amount is required'})
        
        try:
            amount = Decimal(str(amount))
        except:
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be positive'})
        
        note = data.get('note', '')
        
        with transaction.atomic():
            settlement = Settlement.objects.create(
                group=group,
                payer=payer,
                receiver=receiver,
                amount=amount,
                note=note,
                created_by=request.user
            )

            BalanceCalculator.recalculate_group_balances(group)
        
        return JsonResponse({
            'success': True,
            'settlement_id': settlement.id,
            'message': f'Payment of ₹{amount} recorded successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Server error occurred'}, status=500)


@login_required
@require_http_methods(["POST"])
def simplify_group_debts(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.user not in group.members.all():
        return JsonResponse({'success': False, 'error': 'Not a group member'}, status=403)
    
    try:
        with transaction.atomic():
            preview = BalanceCalculator.get_simplification_preview(group)
            
            if not preview['worth_simplifying']:
                return JsonResponse({
                    'success': True,
                    'message': 'Debts are already simplified! No changes needed.',
                    'before': preview['current_transactions'],
                    'after': preview['simplified_transactions']
                })
            
            simplified = BalanceCalculator.simplify_debts(group)
            
            Balance.objects.filter(group=group).delete()
            
            if simplified:
                Balance.objects.bulk_create(simplified)
            
            return JsonResponse({
                'success': True,
                'message': f'Debts simplified! Reduced from {preview["current_transactions"]} to {preview["simplified_transactions"]} transactions.',
                'before': preview['current_transactions'],
                'after': preview['simplified_transactions'],
                'saved': preview['transactions_saved'],
                'percentage_saved': preview['percentage_saved']
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def simplification_preview_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group")
        return redirect('dashboard')
    
    preview = BalanceCalculator.get_simplification_preview(group)
    
    context = {
        'group': group,
        'preview': preview,
    }
    
    return render(request, 'balances/simplification_preview.html', context)

@login_required
def settlements_history_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group")
        return redirect('dashboard')
    
    settlements = Settlement.objects.filter(group=group).select_related(
        'payer', 'receiver', 'created_by'
    ).order_by('-settled_at')
    
    context = {
        'group': group,
        'settlements': settlements,
    }
    
    return render(request, 'balances/settlements_history.html', context)
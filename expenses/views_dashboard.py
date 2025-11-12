# ============================================================================
# ENHANCED DASHBOARD VIEW with Analytics
# expenses/views_dashboard.py
# ============================================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncWeek
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

from groups.models import Group
from expenses.models import Expense
from balances.services import BalanceCalculator
from activity.models import Activity
from balances.models import Balance
from balances.services import BalanceCalculator


@login_required
def dashboard_view(request):
    groups = Group.objects.filter(members=request.user).distinct()

    for group in Group.objects.all():
        if not Balance.objects.filter(group=group).exists():
            BalanceCalculator.recalculate_group_balances(group)

    groups = Group.objects.filter(members=request.user).distinct()
    total_groups = groups.count()
    
    expenses = Expense.objects.filter(
        group__in=groups
    ).select_related('paid_by', 'group').order_by('-date')
    
    total_expenses = expenses.count()

    user_balances = BalanceCalculator.get_user_balances(request.user)
    overall_balance = user_balances.get('net_balance', Decimal('0'))
    total_owes = user_balances.get('total_owes', Decimal('0'))
    total_owed = user_balances.get('total_owed', Decimal('0'))


    recent_expenses = expenses[:10]
    
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_expenses = expenses.filter(
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')
    
    monthly_data = {
        'labels': [],
        'amounts': [],
        'counts': []
    }
    for item in monthly_expenses:
        monthly_data['labels'].append(item['month'].strftime('%b %Y'))
        monthly_data['amounts'].append(float(item['total']))
        monthly_data['counts'].append(item['count'])
    
    category_breakdown = defaultdict(Decimal)
    for expense in expenses[:100]:  
        category_breakdown[expense.group.name] += expense.amount
    
    category_data = {
        'labels': list(category_breakdown.keys())[:5],  
        'amounts': [float(v) for v in list(category_breakdown.values())[:5]]
    }
    
    total_paid_by_user = expenses.filter(paid_by=request.user).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    total_all_expenses = expenses.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('1')  
    
    contribution_percentage = (total_paid_by_user / total_all_expenses * 100) if total_all_expenses else 0
    
    recent_activity = Activity.objects.filter(
        Q(user=request.user) | Q(group__in=groups)
    ).select_related('user', 'group').order_by('-created_at')[:10]
    
    top_spenders = expenses.values(
        'paid_by__username', 'paid_by__id'
    ).annotate(
        total_paid=Sum('amount'),
        expense_count=Count('id')
    ).order_by('-total_paid')[:5]

    settlements_this_month = Activity.objects.filter(
        user=request.user,
        verb='settlement',
        created_at__gte=datetime.now().replace(day=1)
    ).count()


    group_stats = []
    for group in groups[:5]:  
        group_expenses = expenses.filter(group=group)
        total_spent = group_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        expense_count = group_expenses.count()
        
        group_stats.append({
            'group': group,
            'total_spent': total_spent,
            'expense_count': expense_count,
            'average': total_spent / expense_count if expense_count > 0 else Decimal('0')
        })
    
    group_stats.sort(key=lambda x: x['expense_count'], reverse=True)
    
    context = {
        "groups": groups,
        "total_groups": total_groups,
        "total_expenses": total_expenses,
        "total_owes": total_owes,
        "total_owed": total_owed,
        "overall_balance": overall_balance,
        "overall_balance_abs": abs(overall_balance),
        "recent_owes": user_balances.get('owes', [])[:3],
        "recent_owed": user_balances.get('owed', [])[:3],
        "recent_expenses": recent_expenses,
        "recent_activity": recent_activity,
        "monthly_data": monthly_data,
        "category_data": category_data,
        "total_paid_by_user": total_paid_by_user,
        "contribution_percentage": round(contribution_percentage, 1),
        "top_spenders": top_spenders,
        "settlements_this_month": settlements_this_month,
        "group_stats": group_stats,
        "avg_expense": (total_all_expenses / total_expenses) if total_expenses > 0 else Decimal('0'),
        "expenses_this_month": expenses.filter(
            date__gte=datetime.now().replace(day=1)
        ).count(),
    }
    
    return render(request, "expenses/dashboard.html", context)

@login_required
def activity_feed_view(request):
    """Dedicated page for full activity feed"""
    groups = Group.objects.filter(members=request.user)
    
    activities = Activity.objects.filter(
        Q(user=request.user) | Q(group__in=groups)
    ).select_related('user', 'group').order_by('-created_at')[:50]
    
    context = {
        'activities': activities,
    }
    
    return render(request, 'expenses/activity_feed.html', context)

from django.http import JsonResponse

@login_required
def analytics_api(request):
    """API endpoint for fetching analytics data"""
    
    period = request.GET.get('period', '6m')  
    
    groups = Group.objects.filter(members=request.user)
    expenses = Expense.objects.filter(group__in=groups)
    
    if period == '6m':
        start_date = datetime.now() - timedelta(days=180)
    elif period == '1y':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = None
    
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    
    monthly_trend = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    data = {
        'monthly_trend': [
            {
                'month': item['month'].strftime('%Y-%m'),
                'total': float(item['total'])
            }
            for item in monthly_trend
        ],
        'total_spent': float(expenses.aggregate(total=Sum('amount'))['total'] or 0),
        'expense_count': expenses.count(),
    }
    
    return JsonResponse(data)
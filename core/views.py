from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from groups.models import Group
from balances.utils import group_net_balances, simplify_transactions

@login_required
def dashboard(request):
    groups = request.user.member_groups.all()
    total_groups = groups.count()
    total_expenses = sum(g.expenses.count() for g in groups)
    overall_balance = 0
    for g in groups:
        net = group_net_balances(g)
        overall_balance += net.get(request.user.id, 0)
    return render(request, 'dashboard.html', {
        'groups': groups,
        'total_groups': total_groups,
        'total_expenses': total_expenses,
        'overall_balance': overall_balance,
    })

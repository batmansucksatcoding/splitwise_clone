# groups/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Group
from expenses.models import Expense, ExpenseShare
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def group_list(request):
    """Show all groups that the current user is part of."""
    groups = Group.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
    return render(request, 'groups/group_list.html', {'groups': groups})


from django.db.models import Sum

from django.shortcuts import render, get_object_or_404
from .models import Group
from expenses.models import Expense, ExpenseShare
from django.db.models import Sum

# groups/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from expenses.models import Expense, ExpenseShare
from .models import Group

@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, id=pk)

    # Get all expenses for this group
    expenses = (
        Expense.objects.filter(group=group)
        .select_related('paid_by')
        .prefetch_related('shares__user')
        .order_by('-created_at')
    )

    # Compute per-user owes/owed
    you_owe = 0
    you_are_owed = 0

    for expense in expenses:
        for share in expense.shares.all():
            # if current user owes money
            if share.user == request.user and expense.paid_by != request.user:
                you_owe += float(share.amount)
            # if someone else owes current user
            elif expense.paid_by == request.user and share.user != request.user:
                you_are_owed += float(share.amount)

    net_balance = you_are_owed - you_owe

    # Total group stats
    total_spent = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.count()
    total_members = group.members.count()

    # Prepare expense-share context for HTML loop
    expense_data = []
    for expense in expenses:
        shares_info = []
        for s in expense.shares.all():
            if s.user == request.user and expense.paid_by != request.user:
                status = "You owe ₹{:.2f}".format(s.amount)
            elif expense.paid_by == request.user and s.user != request.user:
                status = "{} owes you ₹{:.2f}".format(s.user.username, s.amount)
            elif s.user == expense.paid_by:
                status = "You paid"
            else:
                status = f"{s.user.username} paid their part"
            shares_info.append({
                "user": s.user,
                "amount": s.amount,
                "status": status
            })
        expense_data.append({
            "expense": expense,
            "shares": shares_info,
        })

    context = {
        "group": group,
        "expenses": expense_data,
        "total_spent": total_spent,
        "total_expenses": total_expenses,
        "total_members": total_members,
        "total_you_owe": you_owe,
        "total_you_are_owed": you_are_owed,
        "net_balance": net_balance,
    }

    return render(request, "groups/group_detail.html", context)


@login_required
def create_group(request):
    """Create a new group with optional members."""
    if request.method == 'POST':
        name = request.POST.get('group_name')
        gtype = request.POST.get('group_type')
        desc = request.POST.get('description', '')
        start = request.POST.get('start_date') or None
        end = request.POST.get('end_date') or None

        if not name:
            messages.error(request, "Group name is required.")
            return redirect('create_group')

        # Create the group
        group = Group.objects.create(
            name=name,
            type=gtype,
            description=desc,
            created_by=request.user,
            start_date=start,
            end_date=end,
        )

        # Add creator and selected members
        group.members.add(request.user)
        member_ids = request.POST.getlist('members')

        for mid in member_ids:
            try:
                user = User.objects.get(id=mid)
                group.members.add(user)
            except User.DoesNotExist:
                continue

        messages.success(request, 'Group created successfully!')
        return redirect('group_detail', pk=group.pk)

    # Load all other users for selection
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'groups/create_group.html', {'users': users})


@login_required
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk, created_by=request.user)

    if request.method == 'POST':
        group.name = request.POST.get('group_name')
        group.type = request.POST.get('group_type')
        group.description = request.POST.get('description', '')
        group.start_date = request.POST.get('start_date') or None
        group.end_date = request.POST.get('end_date') or None
        group.save()

        messages.success(request, "Group updated successfully!")
        return redirect('group_detail', pk=group.pk)

    return render(request, 'groups/edit_group.html', {'group': group})


@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk, created_by=request.user)

    if request.method == 'POST':
        group.delete()
        messages.success(request, "Group deleted successfully!")
        return redirect('group_list')

    return render(request, 'groups/delete_group.html', {'group': group})


@login_required
def add_member(request, pk):
    group = get_object_or_404(Group, pk=pk)
    users = User.objects.exclude(id__in=group.members.all())

    if request.method == 'POST':
        selected_ids = request.POST.getlist('members')
        for uid in selected_ids:
            try:
                user = User.objects.get(id=uid)
                group.members.add(user)
            except User.DoesNotExist:
                continue
        messages.success(request, "Members added successfully!")
        return redirect('group_detail', pk=group.pk)

    return render(request, 'groups/add_member.html', {'group': group, 'users': users})


@login_required
def remove_member(request, group_id, user_id):
    """Remove a member from a group."""
    group = get_object_or_404(Group, id=group_id)
    user_to_remove = get_object_or_404(User, id=user_id)

    if request.user == group.created_by or request.user.is_superuser:
        if user_to_remove in group.members.all():
            group.members.remove(user_to_remove)
            messages.success(request, f"{user_to_remove.username} was removed from {group.name}.")
        else:
            messages.warning(request, "That user is not a member of this group.")
    else:
        messages.error(request, "You don’t have permission to remove members from this group.")

    return redirect('group_detail', group_id)


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Group

@login_required
def get_group_members(request, group_id):
    print(f"🔍 DEBUG: get_group_members called for group_id={group_id}")
    try:
        group = Group.objects.get(id=group_id, members=request.user)
    except Group.DoesNotExist:
        print("❌ Group not found or access denied")
        return JsonResponse({"success": False, "error": "Group not found or access denied"}, status=404)

    members = group.members.all()
    print(f"✅ Found members: {[m.username for m in members]}")

    data = [
        {"id": m.id, "username": m.username, "name": m.get_full_name() or m.username}
        for m in members
    ]
    return JsonResponse({"success": True, "members": data})

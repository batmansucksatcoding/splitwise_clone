from xhtml2pdf import pisa
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Expense, ExpenseShare, ExpenseCategory
from groups.models import Group
from accounts.models import User
from balances.services import BalanceCalculator
from notifications.services import NotificationService


@login_required
def expense_list(request):
    """List all expenses for the user"""
    user = request.user

    expenses = Expense.objects.filter(
        Q(paid_by=user) | Q(shares__user=user)
    ).distinct().select_related(
        'paid_by', 'group', 'category'
    ).prefetch_related('shares__user')

    group_id = request.GET.get('group')
    if group_id:
        expenses = expenses.filter(group_id=group_id)

    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category__name=category)

    context = {
        'expenses': expenses,
        'categories': ExpenseCategory.objects.all(),
        'groups': Group.objects.filter(members=user),
        'selected_group': group_id,
        'selected_category': category,
    }

    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_detail(request, expense_id):
    """Show detailed breakdown of an expense"""
    expense = get_object_or_404(
        Expense.objects.select_related('paid_by', 'group', 'category')
                       .prefetch_related('shares__user'),
        id=expense_id
    )

    if not (expense.paid_by == request.user or expense.shares.filter(user=request.user).exists()):
        messages.error(request, "You don't have access to this expense.")
        return redirect('expenses:expense_list')

    total_amount = expense.amount
    shares = expense.shares.all()
    user_share = shares.filter(user=request.user).first()

    amount_owed_to_me = Decimal(0)
    amount_i_owe = Decimal(0)

    if expense.paid_by == request.user:
        amount_owed_to_me = shares.exclude(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        net_balance = amount_owed_to_me
    else:
        amount_i_owe = user_share.amount if user_share else Decimal(0)
        net_balance = -amount_i_owe

    balances = {
        'net_balance': net_balance,
        'owed_to_me': amount_owed_to_me,
        'i_owe': amount_i_owe,
        'details': [
            {
                'user': share.user,
                'amount': share.amount,
                'status': 'owes_me' if expense.paid_by == request.user and share.user != request.user else (
                    'i_owe' if share.user == request.user and expense.paid_by != request.user else 'neutral'
                )
            } for share in shares
        ]
    }

    context = {
        'expense': expense,
        'balances': balances,
    }

    return render(request, 'expenses/expense_detail.html', context)


@login_required
def add_expense(request):
    from datetime import date 

    if request.method == 'POST':
        print("=== ADD EXPENSE DEBUG START ===")
        print("POST DATA:", request.POST)

        title = request.POST.get('title', '').strip()
        amount = Decimal(request.POST.get('amount', '0') or '0')
        group_id = request.POST.get('group')
        paid_by_id = request.POST.get('paid_by')
        split_type = request.POST.get('split_type', 'equal')
        description = request.POST.get('description', '').strip()
        date_value = request.POST.get('date', date.today())

        user_ids = request.POST.getlist('user_ids[]')
        print("DEBUG user_ids:", user_ids)

        if not user_ids:
            messages.error(request, "Please select at least one member.")
            return redirect('add_expense')

        try:
            group = Group.objects.get(id=group_id)
            paid_by = User.objects.get(id=paid_by_id)

            with transaction.atomic():
                expense = Expense.objects.create(
                    description=title or f"Expense on {date_value}",
                    amount=amount,
                    date=date_value,
                    group=group,
                    paid_by=paid_by,
                    split_type=split_type,
                    notes=description
                )
                print("STEP 1: Created Expense:", expense)

                shares = []
                if split_type == 'equal':
                    per_person = (amount / Decimal(len(user_ids))).quantize(Decimal('0.01'))
                    for uid in user_ids:
                        user = User.objects.get(id=uid)
                        shares.append(ExpenseShare(expense=expense, user=user, amount=per_person))
                else:
                    for uid in user_ids:
                        user = User.objects.get(id=uid)
                        shares.append(ExpenseShare(expense=expense, user=user, amount=Decimal('0.00')))

                ExpenseShare.objects.bulk_create(shares)
                print(f"STEP 2: Created {len(shares)} shares")

                BalanceCalculator.recalculate_group_balances(group)
                print("STEP 3: Balances recalculated successfully ✅")

                NotificationService.notify_expense_added(expense)

                messages.success(request, "Expense added successfully!")
                return redirect('dashboard')

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error adding expense: {e}")
            return redirect('add_expense')

    groups = Group.objects.filter(members=request.user)
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'expenses/add_expense.html', {
        'groups': groups,
        'users': users,
        'today': timezone.now().date() 
    })


@login_required
def edit_expense(request, expense_id):
    """Edit an existing expense"""
    expense = get_object_or_404(Expense, id=expense_id, paid_by=request.user)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                expense.description = request.POST['description']
                expense.amount = Decimal(request.POST['amount'])
                expense.currency = request.POST.get('currency', 'INR')
                expense.date = request.POST['date']
                expense.notes = request.POST.get('notes', '')
                expense.category_id = request.POST.get('category') if request.POST.get('category') else None
                expense.split_type = request.POST['split_type']
                expense.save()

                expense.shares.all().delete()

                split_type = request.POST['split_type']
                user_ids = request.POST.getlist('user_ids[]')
                print("DEBUG user_ids:", user_ids)

                if split_type == 'equal':
                    num_people = len(user_ids)
                    if num_people <= 0:
                        messages.error(request, "No participants selected for this expense.")
                        expense.delete()
                        return redirect('expenses:add_expense')

                    share_amount = (expense.amount / num_people).quantize(Decimal('0.01'))
                    for user_id in user_ids:
                        ExpenseShare.objects.create(
                            expense=expense,
                            user_id=user_id,
                            amount=share_amount
                        )

                elif split_type == 'unequal':
                    amounts = request.POST.getlist('amounts[]')
                    total = sum(Decimal(amt) for amt in amounts)

                    if total != expense.amount:
                        raise ValueError(f"Shares don't match expense amount")

                    for user_id, amount in zip(user_ids, amounts):
                        ExpenseShare.objects.create(
                            expense=expense,
                            user_id=user_id,
                            amount=Decimal(amount)
                        )

                elif split_type == 'percentage':
                    percentages = request.POST.getlist('percentages[]')
                    total_pct = sum(Decimal(pct) for pct in percentages)

                    if total_pct != 100:
                        raise ValueError(f"Percentages must sum to 100%")

                    for user_id, percentage in zip(user_ids, percentages):
                        pct = Decimal(percentage)
                        amount = (expense.amount * pct / 100).quantize(Decimal('0.01'))

                        ExpenseShare.objects.create(
                            expense=expense,
                            user_id=user_id,
                            amount=amount,
                            percentage=pct
                        )

                NotificationService.notify_expense_edited(expense, request.user)

                messages.success(request, "Expense updated successfully!")
                return redirect('expenses:expense_detail', expense_id=expense.id)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error updating expense: {str(e)}")

    context = {
        'expense': expense,
        'groups': Group.objects.filter(members=request.user),
        'categories': ExpenseCategory.objects.all(),
        'shares': expense.shares.all(),
    }

    return render(request, 'expenses/edit_expense.html', context)


@login_required
def delete_expense(request, expense_id):
    try:
        expense = Expense.objects.get(id=expense_id)
    except Expense.DoesNotExist:
        messages.error(request, "Expense not found.")
        return redirect('expenses:expense_list')

    if expense.paid_by != request.user:
        messages.error(request, "Only the payer can delete this expense.")
        return redirect('expenses:expense_list')

    if request.method == 'POST':
        expense_desc = expense.description
        group = expense.group

        expense_data = {
            'description': expense.description,
            'group': expense.group,
            'affected_users': list(expense.shares.values_list('user', flat=True))
        }
        expense_data['affected_users'] = User.objects.filter(id__in=expense_data['affected_users'])

        expense.delete()

        BalanceCalculator.recalculate_group_balances(group)

        NotificationService.notify_expense_deleted(expense_data, request.user)

        messages.success(request, f"Expense '{expense_desc}' deleted successfully!")
        return redirect('expenses:expense_list')

    return render(request, 'expenses/delete_expense.html', {'expense': expense})


@login_required
def my_balances(request):
    user = request.user

    balances = calculate_user_balances(user)

    context = {
        'total_owed_to_me': balances['owed_to_me'],
        'total_i_owe': balances['i_owe'],
        'net_balance': balances['net_balance'],
        'details': balances['details'],
    }

    return render(request, 'expenses/my_balances.html', context)


def calculate_user_balances(user):
    from collections import defaultdict

    balances = defaultdict(Decimal)

    paid_expenses = Expense.objects.filter(paid_by=user).prefetch_related('shares__user')

    for expense in paid_expenses:
        for share in expense.shares.all():
            if share.user != user:
                balances[share.user] += share.amount

    shared_expenses = Expense.objects.filter(shares__user=user).select_related('paid_by')

    for expense in shared_expenses:
        if expense.paid_by != user:
            user_share = expense.get_share_for_user(user)
            balances[expense.paid_by] -= user_share

    owed_to_me = sum(amt for amt in balances.values() if amt > 0)
    i_owe = sum(abs(amt) for amt in balances.values() if amt < 0)

    details = []
    for other_user, amount in balances.items():
        if amount != 0:
            details.append({
                'user': other_user,
                'amount': abs(amount),
                'status': 'owes_me' if amount > 0 else 'i_owe'
            })

    details.sort(key=lambda x: x['amount'], reverse=True)

    return {
        'owed_to_me': owed_to_me,
        'i_owe': i_owe,
        'net_balance': owed_to_me - i_owe,
        'details': details
    }

@login_required
def get_group_members(request, group_id):
    group = get_object_or_404(Group, id=group_id, members=request.user)

    members = [
        {
            'id': member.id,
            'username': member.username,
            'name': getattr(member, 'profile', None).display_name if hasattr(member, 'profile') else member.username,
        }
        for member in group.members.all()
    ]

    return JsonResponse({'members': members})

from django.template.loader import get_template
from django.http import HttpResponse

import io

@login_required
def expense_pdf(request, expense_id):
    """Generate a downloadable PDF directly from expense_detail.html."""
    expense = get_object_or_404(
        Expense.objects.select_related('paid_by', 'group', 'category')
                       .prefetch_related('shares__user'),
        id=expense_id
    )

    # ✅ same access check as expense_detail
    if not (expense.paid_by == request.user or expense.shares.filter(user=request.user).exists()):
        messages.error(request, "You don't have access to this expense.")
        return redirect('expenses:expense_list')

    # ✅ reuse your balance logic
    shares = expense.shares.all()
    user_share = shares.filter(user=request.user).first()
    amount_owed_to_me = Decimal(0)
    amount_i_owe = Decimal(0)

    if expense.paid_by == request.user:
        amount_owed_to_me = shares.exclude(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        net_balance = amount_owed_to_me
    else:
        amount_i_owe = user_share.amount if user_share else Decimal(0)
        net_balance = -amount_i_owe

    balances = {
        'net_balance': net_balance,
        'owed_to_me': amount_owed_to_me,
        'i_owe': amount_i_owe,
        'details': [
            {
                'user': share.user,
                'amount': share.amount,
                'status': 'owes_me' if expense.paid_by == request.user and share.user != request.user else (
                    'i_owe' if share.user == request.user and expense.paid_by != request.user else 'neutral'
                )
            } for share in shares
        ]
    }

    context = {
        'expense': expense,
        'balances': balances,
        'user': request.user,
        'pdf_mode': True,   # 👈 tells template to hide buttons/nav when rendering PDF
    }

    # ✅ render same template as on-screen
    template = get_template('expenses/expense_detail.html')
    html = template.render(context)

    # ✅ convert HTML to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="expense_{expense.id}.pdf"'

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

    if pisa_status.err:
        return HttpResponse("Error generating PDF.<pre>" + html + "</pre>")

    response.write(pdf_buffer.getvalue())
    return response

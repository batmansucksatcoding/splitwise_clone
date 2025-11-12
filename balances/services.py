from django.db import transaction
from django.db.models import Q
from collections import defaultdict
from decimal import Decimal
import heapq
from .models import Balance, Settlement

class BalanceCalculator:
    """Handles all balance calculations and debt simplification"""

    @staticmethod
    def recalculate_group_balances(group):
        """Recalculate all balances for a group from scratch"""
        from expenses.models import Expense

        expenses = Expense.objects.filter(group=group).prefetch_related('shares__user')
        net_balances = defaultdict(Decimal)

        for expense in expenses:
            paid_by = expense.paid_by
            amount = expense.amount
            shares = expense.shares.all()

            if not shares or len(shares) == 0:
                print(f"⚠️ Skipping expense '{expense.description}' — no shares found.")
                continue

            if expense.split_type == 'equal':
                try:
                    per_person = amount / Decimal(len(shares))
                except Exception as e:
                    print(f"⚠️ Division error in expense '{expense.description}': {e}")
                    continue

                for share in shares:
                    if share.user_id != paid_by.id:
                        net_balances[share.user_id] -= per_person
                        net_balances[paid_by.id] += per_person

            elif expense.split_type == 'unequal':
                for share in shares:
                    if share.user_id != paid_by.id:
                        net_balances[share.user_id] -= share.amount
                        net_balances[paid_by.id] += share.amount

            elif expense.split_type == 'percentage':
                for share in shares:
                    if share.user_id != paid_by.id and share.percentage is not None:
                        owed = (amount * share.percentage) / 100
                        net_balances[share.user_id] -= owed
                        net_balances[paid_by.id] += owed

        settlements = Settlement.objects.filter(group=group)
        for settlement in settlements:
            net_balances[settlement.payer_id] += settlement.amount
            net_balances[settlement.receiver_id] -= settlement.amount

        Balance.objects.filter(group=group).delete()
        balances_to_create = []

        user_ids = list(net_balances.keys())

        for i, user1_id in enumerate(user_ids):
            for user2_id in user_ids[i + 1:]:
                balance1 = net_balances[user1_id]
                balance2 = net_balances[user2_id]

                if balance1 < 0 and balance2 > 0:
                    amount = min(abs(balance1), balance2)
                    if amount > Decimal('0.01'):
                        balances_to_create.append(Balance(
                            group=group,
                            from_user_id=user1_id,
                            to_user_id=user2_id,
                            amount=amount
                        ))
                elif balance2 < 0 and balance1 > 0:
                    amount = min(abs(balance2), balance1)
                    if amount > Decimal('0.01'):
                        balances_to_create.append(Balance(
                            group=group,
                            from_user_id=user2_id,
                            to_user_id=user1_id,
                            amount=amount
                        ))

        if balances_to_create:
            Balance.objects.bulk_create(balances_to_create)

    @staticmethod
    def get_user_balances(user, group=None):
        """Get all balances for a user"""
        filters = Q(from_user=user) | Q(to_user=user)
        if group:
            filters &= Q(group=group)

        balances = Balance.objects.filter(filters).select_related('group', 'from_user', 'to_user')

        owes = []
        owed = []

        for balance in balances:
            if balance.from_user == user:
                owes.append({'user': balance.to_user, 'group': balance.group, 'amount': balance.amount})
            else:
                owed.append({'user': balance.from_user, 'group': balance.group, 'amount': balance.amount})

        return {
            'owes': owes,
            'owed': owed,
            'total_owes': sum(item['amount'] for item in owes),
            'total_owed': sum(item['amount'] for item in owed),
            'net_balance': sum(item['amount'] for item in owed) - sum(item['amount'] for item in owes),
        }

    @staticmethod
    def simplify_debts(group):
        balances = Balance.objects.filter(group=group)
        net_balances = defaultdict(Decimal)
        
        for balance in balances:
            net_balances[balance.from_user_id] -= balance.amount
            net_balances[balance.to_user_id] += balance.amount
        creditors = []  
        debtors = []    

        for user_id, amount in net_balances.items():
            if amount > Decimal('0.01'):
                heapq.heappush(creditors, (-amount, user_id))
            elif amount < Decimal('-0.01'):
                heapq.heappush(debtors, (amount, user_id))

        simplified_balances = []

        while creditors and debtors:
            credit_amount, creditor_id = heapq.heappop(creditors)
            credit_amount = -credit_amount 
        
            debt_amount, debtor_id = heapq.heappop(debtors)
            debt_amount = abs(debt_amount)

            settlement_amount = min(credit_amount, debt_amount)

            simplified_balances.append(Balance(
                group=group,
                from_user_id=debtor_id,
                to_user_id=creditor_id,
                amount=settlement_amount
            ))

            if credit_amount > settlement_amount:
                heapq.heappush(creditors, (-(credit_amount - settlement_amount), creditor_id))
            
            if debt_amount > settlement_amount:
                heapq.heappush(debtors, (-(debt_amount - settlement_amount), debtor_id))

        return simplified_balances

    @staticmethod
    def get_group_balance_matrix(group):
        balances = Balance.objects.filter(group=group).select_related('from_user', 'to_user')
        members = list(group.members.all())
        member_ids = [m.id for m in members]

        matrix = {m.id: {mid: Decimal('0') for mid in member_ids} for m in members}

        for balance in balances:
            matrix[balance.from_user_id][balance.to_user_id] = balance.amount

        return {'members': members, 'matrix': matrix}

    @staticmethod
    def get_simplification_preview(group):
        current_balances = Balance.objects.filter(group=group).select_related('from_user', 'to_user')
        current_count = current_balances.count()
        
        simplified = BalanceCalculator.simplify_debts(group)
        simplified_count = len(simplified)
        
        transactions_saved = current_count - simplified_count
        percentage_saved = (transactions_saved / current_count * 100) if current_count > 0 else 0
        
        return {
            'current_transactions': current_count,
            'simplified_transactions': simplified_count,
            'transactions_saved': transactions_saved,
            'percentage_saved': round(percentage_saved, 1),
            'current_balances': list(current_balances),
            'simplified_balances': simplified,
            'worth_simplifying': transactions_saved > 0
        }
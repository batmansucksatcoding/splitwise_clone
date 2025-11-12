from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from expenses.models import Expense
from groups.models import Group

def round2(v):
    return float(Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def group_net_balances(group: Group):
    """
    Return dict user_id -> net balance (positive = others owe them; negative = they owe)
    We calculate: for each expense, each participant owes their share; paid_by covered full amount.
    """
    net = defaultdict(float)
    for expense in group.expenses.all():
        splits = expense.compute_splits()  
        payer_id = str(expense.paid_by_id)
        net[payer_id] += float(expense.amount)
        for uid, amt in splits.items():
            net[str(uid)] -= float(amt)
    return {int(k): round2(v) for k,v in net.items()}

def simplify_transactions(net_balances):
    """
    Take net_balances dict user_id->float and return list of minimal transactions:
    [(from_user_id, to_user_id, amount), ...]
    Greedy algorithm: match biggest creditor with biggest debtor.
    """
    creditors = []
    debtors = []
    for uid, bal in net_balances.items():
        if bal > 0: creditors.append([uid, bal])
        elif bal < 0: debtors.append([uid, -bal])  
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    i=j=0
    txs=[]
    while i < len(creditors) and j < len(debtors):
        cid, camt = creditors[i]
        did, damt = debtors[j]
        amt = min(camt, damt)
        txs.append( (did, cid, round2(amt)) )  
        creditors[i][1] -= amt
        debtors[j][1] -= amt
        if abs(creditors[i][1]) < 0.01: i += 1
        if abs(debtors[j][1]) < 0.01: j += 1
    return txs
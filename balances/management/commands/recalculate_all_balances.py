from django.core.management.base import BaseCommand
from groups.models import Group
from balances.services import BalanceCalculator

class Command(BaseCommand):
    help = 'Recalculate balances for all groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group-id',
            type=int,
            help='Recalculate for specific group only',
        )

    def handle(self, *args, **options):
        group_id = options.get('group_id')
        
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                self.stdout.write(f'Recalculating balances for group: {group.name}')
                BalanceCalculator.recalculate_group_balances(group)
                self.stdout.write(self.style.SUCCESS(f'✓ Done for {group.name}'))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Group with ID {group_id} not found'))
        else:
            groups = Group.objects.all()
            total = groups.count()
            self.stdout.write(f'Recalculating balances for {total} groups...')
            
            for i, group in enumerate(groups, 1):
                self.stdout.write(f'[{i}/{total}] Processing: {group.name}')
                BalanceCalculator.recalculate_group_balances(group)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully recalculated {total} groups'))
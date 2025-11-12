from .models import Activity
def log(user, verb, target_type=None, target_id=None, data=None):
    Activity.objects.create(user=user, verb=verb, target_type=target_type, target_id=target_id, data=data or {})
from .models import Friendship

def get_friends(user):
    """Return queryset of all accepted friends of a user."""
    sent = Friendship.objects.filter(from_user=user, accepted=True).values_list('to_user', flat=True)
    received = Friendship.objects.filter(to_user=user, accepted=True).values_list('from_user', flat=True)
    friend_ids = list(sent) + list(received)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(id__in=friend_ids)

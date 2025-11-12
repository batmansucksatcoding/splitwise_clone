from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from . import models
from .models import Friendship

User = get_user_model()

@login_required
def friends_list(request):
    # get all friendships where current user is involved
    friends = Friendship.objects.filter(user=request.user) | Friendship.objects.filter(friend=request.user)
    return render(request, 'users/friends_list.html', {'friends': friends})

@login_required
def add_friend(request, user_id):
    friend_user = get_object_or_404(User, id=user_id)
    if friend_user == request.user:
        messages.error(request, "You can’t add yourself.")
    else:
        # create symmetrical friendship (both ways)
        Friendship.objects.get_or_create(user=request.user, friend=friend_user)
        Friendship.objects.get_or_create(user=friend_user, friend=request.user)
        messages.success(request, f"{friend_user.username} added as a friend!")
    return redirect('friends_list')

@login_required
def remove_friend(request, user_id):
    friend_user = get_object_or_404(User, id=user_id)
    Friendship.objects.filter(user=request.user, friend=friend_user).delete()
    Friendship.objects.filter(user=friend_user, friend=request.user).delete()
    messages.info(request, f"Removed {friend_user.username} from your friends.")
    return redirect('friends_list')

@login_required
def find_friends(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)

    return render(request, 'users/find_friends.html', {'results': results, 'query': query})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from users.models import Friendship
from django.db.models import Q

User = get_user_model()

@login_required
def friends_list(request):
    friends = User.objects.filter(
        Q(friends_of__user=request.user) | Q(friendships__friend=request.user)
    ).distinct()
    return render(request, "users/friends_list.html", {"friends": friends})

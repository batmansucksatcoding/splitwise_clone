# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Friendship
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def add_friend(request, friend_id):
    friend = User.objects.get(id=friend_id)
    if friend == request.user:
        messages.warning(request, "You can't add yourself.")
    else:
        Friendship.objects.get_or_create(user=request.user, friend=friend)
        Friendship.objects.get_or_create(user=friend, friend=request.user)  # mutual friendship
        messages.success(request, f"{friend.username} added as friend!")
    return redirect('friends_list')

@login_required
def friends_list(request):
    # Get friendships where the current user is either user or friend
    friendships = Friendship.objects.filter(user=request.user) | Friendship.objects.filter(friend=request.user)

    # Extract the "other side" of each friendship
    friends = []
    for f in friendships:
        if f.user == request.user:
            friends.append(f.friend)
        else:
            friends.append(f.user)

    return render(request, 'users/friends_list.html', {'friends': friends})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Friendship
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if not request.POST.get('terms'):
            messages.error(request, 'You must agree to the Terms of Service and Privacy Policy.')
            return render(request, 'registration/register.html', {'form': form})

        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, f'Account created successfully for {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                if not request.POST.get('remember_me'):
                    request.session.set_expiry(0)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'expenses/dashboard.html', {'user': request.user})

def terms_of_service(request):
    return render(request, 'accounts/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

User = get_user_model()

@login_required
def friends_list_view(request):
    """Show user's accepted friends and pending friend requests."""
    friendships = Friendship.objects.filter(
        Q(requester=request.user, status='accepted') |
        Q(receiver=request.user, status='accepted')
    ).select_related('requester', 'receiver')

    friends = [
        f.receiver if f.requester == request.user else f.requester
        for f in friendships
    ]

    requests = Friendship.objects.filter(receiver=request.user, status='pending')

    context = {
        'friends': friends,
        'requests': requests,
    }
    return render(request, 'users/friends.html', context)

@login_required
def add_friend_view(request, user_id):
    """Send a friend request"""
    receiver = get_object_or_404(User, id=user_id)

    if receiver == request.user:
        messages.error(request, "You cannot add yourself as a friend.")
        return redirect('search_friends')

    existing = Friendship.objects.filter(
        Q(requester=request.user, receiver=receiver) |
        Q(requester=receiver, receiver=request.user)
    ).first()

    if existing:
        messages.info(request, "Friend request already exists.")
    else:
        Friendship.objects.create(requester=request.user, receiver=receiver)
        messages.success(request, f"Friend request sent to {receiver.username}!")

    return redirect('friends_list')

@login_required
def accept_request_view(request, request_id):
    """Accept an incoming friend request"""
    fr = get_object_or_404(Friendship, id=request_id, receiver=request.user)
    fr.status = 'accepted'
    fr.save()
    messages.success(request, f"You are now friends with {fr.requester.username}!")
    return redirect('friends_list')

@login_required
def search_friends_view(request):
    """Search for users by username or email"""
    query = request.GET.get('q', '')
    results = []

    if query:
        results = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)

    return render(request, 'accounts/friends_search.html', {
        'results': results,
        'query': query,
    })

def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        messages.success(request, f"If an account with {email} exists, the password has been reset.")
    return render(request, 'registration/password_reset.html')
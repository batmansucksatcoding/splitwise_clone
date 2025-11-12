from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, RegisterSerializer, FriendshipSerializer
from .models import Friendship

User = get_user_model()

class RegisterViewSet(viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

class FriendshipViewSet(viewsets.ModelViewSet):
    """Send, list, accept, reject friend requests + suggestions + search."""
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(
            Q(requester=user) | Q(receiver=user)
        ).select_related('requester', 'receiver').order_by('-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        """Create a friend request (pending)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        friendship = Friendship(
            requester=request.user,
            receiver=serializer.validated_data['receiver'],
            status='pending'
        )
        friendship.full_clean()  
        friendship.save()
        read_serializer = self.get_serializer(friendship)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        fr = self.get_object()
        if fr.receiver != request.user:
            return Response({'detail': 'You are not the receiver of this request.'},
                            status=status.HTTP_403_FORBIDDEN)
        fr.status = 'accepted'
        fr.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(fr).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        fr = self.get_object()
        if fr.receiver != request.user:
            return Response({'detail': 'You are not the receiver of this request.'},
                            status=status.HTTP_403_FORBIDDEN)
        fr.status = 'rejected'
        fr.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(fr).data)

    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Suggest users who aren’t already friends with you."""
        user = request.user
        existing = Friendship.objects.filter(
            Q(requester=user, status='accepted') |
            Q(receiver=user, status='accepted')
        )
        friend_ids = set(
            list(existing.values_list('requester_id', flat=True)) +
            list(existing.values_list('receiver_id', flat=True))
        )
        friend_ids.add(user.id)

        suggestions = User.objects.exclude(id__in=friend_ids).order_by('id')[:10]
        return Response(UserSerializer(suggestions, many=True).data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users by username or name."""
        q = request.GET.get('q', '').strip()
        if not q:
            return Response([], status=status.HTTP_200_OK)

        users = User.objects.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).exclude(id=request.user.id).order_by('id')[:10]

        return Response(UserSerializer(users, many=True).data)
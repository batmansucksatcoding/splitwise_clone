from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class User(AbstractUser):
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    default_currency = models.CharField(max_length=10, default='INR')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')

    def __str__(self):
        return self.get_full_name() or self.username

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friend_requests_sent',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friend_requests_received',
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('requester', 'receiver')
        ordering = ['-created_at']

    def clean(self):
        if self.requester_id and self.receiver_id and self.requester_id == self.receiver_id:
            raise ValidationError("You cannot send a friend request to yourself.")

    def __str__(self):
        return f"{self.requester} -> {self.receiver} ({self.status})"
from django.db import models
from django.conf import settings

class Group(models.Model):
    GROUP_TYPES = [
        ('trip','Trip'),
        ('home','Home / Flatmates'),
        ('couple','Couple'),
        ('event','Event'),
        ('other','Others'),
    ]
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=20, choices=GROUP_TYPES, default='other')
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='member_groups')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='groups_created')

    def __str__(self):
        return self.name

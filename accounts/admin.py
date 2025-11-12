from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Friendship
User = get_user_model()
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username','email','first_name','last_name')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('id','requester','receiver','status','created_at')
    list_filter = ('status',)

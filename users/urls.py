from django.urls import path
from . import views_friends
from . import views_profile , views_friends
from .views_friends import friends_list

urlpatterns = [
    # path('friends/', views_friends.friends_list, name='friends_list'),
    path('friends/add/<int:user_id>/', views_friends.add_friend, name='add_friend'),
    path('friends/remove/<int:user_id>/', views_friends.remove_friend, name='remove_friend'),
    path('friends/find/', views_friends.find_friends, name='find_friends'),
    path('profile/', views_profile.profile_view, name='profile'),
    path('profile/edit/', views_profile.edit_profile, name='edit_profile'),
    path("friends/", friends_list, name="friends_list"),

]

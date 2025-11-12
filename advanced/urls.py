from django.urls import path
from . import views

urlpatterns = [
    path('', views.advanced_features, name='advanced_features'),
]

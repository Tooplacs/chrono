from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('api/pointages/', views.get_pointages),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.access_log_list, name='access_log'),
]

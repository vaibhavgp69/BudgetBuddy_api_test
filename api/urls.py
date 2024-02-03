from django.urls import path
from .views import *
from . import views
from django.urls import include, re_path

from rest_framework.authtoken.views import obtain_auth_token


from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('newuser', views.UserView.as_view(), name = 'newuser'),
    path('newtrans', views.TransactionView.as_view(), name = 'newtrans'),
]
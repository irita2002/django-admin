from django.urls import path
from . import views


urlpatterns = [
    path('auth/login/', views.sign_in, name='login'),
    path('logout/', views.sign_out, name='logout'),
]

from django.urls import path
from .views import DashboardsView



urlpatterns = [
    path(
        "",
        DashboardsView,
        name="index",
    )
]

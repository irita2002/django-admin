from django.urls import path
from .views import DashboardsView



urlpatterns = [
    path(
        "dash/",
        DashboardsView,
        name="index",
    )
]

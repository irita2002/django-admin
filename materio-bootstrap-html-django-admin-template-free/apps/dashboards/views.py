from django.views.generic import TemplateView
from web_project import TemplateLayout
from .decorators import login_required_custom
import requests
from django.shortcuts import render
"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to dashboards/urls.py file for more pages.
"""
@login_required_custom
def DashboardsView(request):
    # Predefined function
    return render(request,'dashboard_analytics.html')

from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.shortcuts import render
from .forms import LoginForm
from web_project.template_helpers.theme import TemplateHelper

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import LoginForm


def sign_in(request):

    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/')
        form = LoginForm()
        return render(request,'auth_login_basic.html', {'form': form,'layout_path': TemplateHelper.set_layout("layout_blank.html"),})
    
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request,username=username,password=password)
            if user:
                login(request, user)
                messages.success(request,f'Hi {username.title()}, Bienvenido otra vez!')
                return redirect('/')
        
        # form is not valid or user is not authenticated
        messages.error(request,'Contaseña o usuario incorrecto')
        return render(request,'auth_login_basic.html',{'form': form,'layout_path': TemplateHelper.set_layout("layout_blank.html"),})

def sign_out(request):
    logout(request)
    messages.success(request,f'Estas deslogueado.')
    return redirect('login')   
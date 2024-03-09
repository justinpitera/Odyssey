# accounts/views.py

from multiprocessing import AuthenticationError
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')  
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form, 'page_title': 'Register - Odyssey'})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('map') 
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form, 'page_title': 'Login - Odyssey'})

def logout_view(request):
    logout(request)
    return redirect('login')



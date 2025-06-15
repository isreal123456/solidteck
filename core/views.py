from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm, CustomLoginForm

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('admin_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect_user_based_on_role(user)
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def redirect_user_based_on_role(user):
    if user.role == 'admin_panel':
        return redirect('admin_dashboard')
    elif user.role == 'storekeeper':
        return redirect('inventory_dashboard')
    elif user.role == 'salesperson':
        return redirect('dashboard_sale')
    return redirect('login')  # fallback

def home_view(request):
    return render(request, 'core/home.html')

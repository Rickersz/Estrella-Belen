from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.utils.crypto import get_random_string
from django.contrib import messages
from .models import CustomUser, PasswordResetRequest

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # handle existing user case
        if CustomUser.objects.filter(email= email).exists():
            return render(request, 'authentication/register.html', {'error': 'Email already in use. Please sign up with a different email or login.'})

        # Handle password mismatch
        if password != confirm_password:
            return render(request, 'authentication/register.html', {'error': 'Passwords do not match.'})

        # create user logic goes here
        user = CustomUser.objects.create_user(  # create_user is a method provided by AbstractUser (ensure password is hashed & default fields are handled -> create won't work here)
            # username=email,w
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        login(request, user)
        return redirect('student_list')     # redirect to dashboard later based on user role
    return render(request, 'authentication/register.html')

from django.contrib.auth import authenticate
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password) # get the authenticated user object
        if user is not None:
            login(request, user)
            return redirect('student_list')  # redirect to dashboard later based on user role
        return render(request, 'authentication/login.html', {'error': 'Invalid email or password.'})

    return render(request, 'authentication/login.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = CustomUser.objects.filter(email=email).first()
        if user:
            token = get_random_string(length=32)
            reset_request = PasswordResetRequest.objects.create(user=user, email=email, token=token)
            reset_request.send_reset_email(request)
            
            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('forgot_password')
        
        messages.error(request, 'User with this email does not exist.')
        return redirect('forgot_password')
    return render(request, 'authentication/forgot-password.html')

def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).first()
    if not (reset_request and reset_request.is_valid):    # doesn't check for 2nd condition if reset_request is None
        messages.error(request, 'The password reset link is invalid or has expired. Please request a new one.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            return render(request, 'authentication/reset-password.html', {'error': 'Passwords do not match.', 'token': token})
        
        reset_request.user.set_password(new_password)       # hash the new password
        reset_request.user.save()
        reset_request.delete()  # Invalidate the used token

        messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
        return redirect('login')
    return render(request, 'authentication/reset-password.html', {'token': token})


def logout_view(request):
    logout(request)
    return redirect('login')
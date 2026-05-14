from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from home_auth.models import CustomUser
from .forms import UserCreationForm, UserEditForm
from school import context_processors
from .models import Notification
from student.models import Student
from department.models import Department


@login_required(login_url='login')
def index(request):
    dashboards = context_processors.dashboards(request)['dashboards']

    if len(dashboards) >= 1:
     # multiples roles: render default at '/' and selected dashboard would be at dashboard/<role> URL
        dash = dashboards[0]['url_name']  # Default to first role
        if dash == 'admin_dashboard':
            return render(request, 'home/index.html', {'dashboards': dashboards})
        elif dash == 'teacher_dashboard':
            return render(request, 'teacher/teacher-dashboard.html', {'dashboards': dashboards})
        elif dash == 'student_dashboard':
            return render(request, 'student/student-dashboard.html', {'dashboards': dashboards})
    else:
        return redirect('login')  # No valid role found, redirect to login


def is_admin(user):
    return hasattr(user, 'is_admin') and user.is_admin
def is_teacher(user):
    return hasattr(user, 'is_teacher') and user.is_teacher
def is_student(user):
    return hasattr(user, 'is_student') and user.is_student


#region dashboard views
# protected views for each dashboard
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    context = {
        'students': Student.objects.all(),
        'departments': Department.objects.all(),
    }
    return render(request, 'home/index.html', context)

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='login')
def teacher_dashboard(request):
    return render(request, 'teacher/teacher-dashboard.html')

@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def student_dashboard(request):
    return render(request, 'student/student-dashboard.html')
#endregion


def create_notification(user, message):
    if user.is_authenticated:
        Notification.objects.create(user=user, message=message)        # create notification object in the database
    
@login_required(login_url='login')
def dashboard(request):
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    context = {
        'notifications': unread_notifications,
    }
    return render(request, 'student/student-dashboard.html', context)


#region notifications
@login_required(login_url='login')
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    print('\n\nNotification ID:', notification_id)
    print('Notification Object:', notification)
    if request.method == 'POST' and notification:
        notification.is_read = True
        notification.save()     # mark as read
        
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

@login_required(login_url='login')
def clear_notifications(request):
    if request.method == 'POST':
        notifications = Notification.objects.filter(user=request.user)
        notifications.delete()
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

@login_required(login_url='login')
def show_all_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'notifications': notifications,
    }
    return render(request, 'student/student-dashboard.html', context)
#endregion


@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def user_management(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])    # hash the password before saving
            user.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_management')
        else:
            messages.error(request, 'Error creating user.')
    
    users = CustomUser.objects.all()
    context = {
        'users': users,
        'form': form,
    }
    return render(request, 'home/user_management.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'home/edit_user.html', {'form': form, 'user': user})
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Sum
from autenticacion.models import CustomUser
from .forms import UserCreationForm, UserEditForm
from escuela import context_processors
from .models import Notification
from estudiante.models import Student
from profesor.models import Teacher
from materia.models import Subject
from bitacora.models import AccessLog
from pagos.models import Payment
from escuela.models import ClassTeacherAssignment


def get_admin_dashboard_context(extra_context=None):
    context = {
        'students_count': Student.objects.count(),
        'teachers_count': Teacher.objects.count(),
        'subjects_count': Subject.objects.count(),
        'access_logs_count': AccessLog.objects.count(),
        'pending_payments_count': Payment.objects.filter(status__in=[Payment.STATUS_PENDING, Payment.STATUS_PARTIAL, Payment.STATUS_OVERDUE]).count(),
        'overdue_payments_count': Payment.objects.filter(status=Payment.STATUS_OVERDUE).count(),
        'payments_debt': Payment.objects.filter(balance__gt=0).aggregate(total=Sum('balance'))['total'] or 0,
        'recent_students': Student.objects.select_related('parent').order_by('-id')[:8],
        'recent_access_logs': AccessLog.objects.select_related('user').order_by('-created_at')[:8],
        'recent_payments': Payment.objects.select_related('student', 'representative').order_by('-updated_at')[:8],
    }
    if extra_context:
        context.update(extra_context)
    return context


@login_required(login_url='iniciar_sesion')
def index(request):
    dashboards = context_processors.dashboards(request)['dashboards']

    if len(dashboards) >= 1:
     # multiples roles: render default at '/' and selected dashboard would be at dashboard/<role> URL
        dash = dashboards[0]['url_name']  # Default to first role
        if dash == 'admin_dashboard':
            return render(request, 'escuela/inicio.html', get_admin_dashboard_context({'dashboards': dashboards}))
        elif dash == 'teacher_dashboard':
            return render(request, 'profesor/panel-profesor.html', {'dashboards': dashboards})
        elif dash == 'student_dashboard':
            return render(request, 'estudiante/panel-estudiante.html', {'dashboards': dashboards})
        elif dash == 'representative_dashboard':
            return representative_dashboard(request)
    else:
        return redirect('iniciar_sesion')  # No valid role found, redirect to login


def is_admin(user):
    return hasattr(user, 'is_admin') and user.is_admin
def is_teacher(user):
    return hasattr(user, 'is_teacher') and user.is_teacher
def is_student(user):
    return hasattr(user, 'is_student') and user.is_student
def is_representative(user):
    return hasattr(user, 'is_representative') and user.is_representative


#region dashboard views
# protected views for each dashboard
@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def admin_dashboard(request):
    return render(request, 'escuela/inicio.html', get_admin_dashboard_context())

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_teacher, login_url='iniciar_sesion')
def teacher_dashboard(request):
    teacher = Teacher.objects.filter(email__iexact=request.user.email).first()
    assignments = ClassTeacherAssignment.objects.select_related('class_assigned', 'subject').filter(teacher=teacher, is_active=True) if teacher else ClassTeacherAssignment.objects.none()
    sections = [assignment.class_assigned for assignment in assignments]
    students = Student.objects.filter(section__in=[section.section for section in sections]).select_related('parent') if sections else Student.objects.none()
    return render(request, 'profesor/panel-profesor.html', {
        'teacher': teacher,
        'assignments': assignments,
        'students': students[:12],
        'sections_count': len(sections),
        'students_count': students.count(),
    })

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_student, login_url='iniciar_sesion')
def student_dashboard(request):
    return render(request, 'estudiante/panel-estudiante.html')

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_representative, login_url='iniciar_sesion')
def representative_dashboard(request):
    parent = getattr(request.user, 'representante', None)
    students = parent.student_set.all() if parent else Student.objects.none()
    payments = Payment.objects.filter(representative=parent).select_related('student') if parent else Payment.objects.none()
    return render(request, 'representante/panel-representante.html', {
        'parent': parent,
        'students': students,
        'payments': payments[:8],
        'pending_payments': payments.filter(balance__gt=0),
        'debt': payments.filter(balance__gt=0).aggregate(total=Sum('balance'))['total'] or 0,
    })
#endregion


def create_notification(user, message):
    if user.is_authenticated:
        Notification.objects.create(user=user, message=message)        # create notification object in the database
    
@login_required(login_url='iniciar_sesion')
def dashboard(request):
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    context = {
        'notifications': unread_notifications,
    }
    return render(request, 'estudiante/panel-estudiante.html', context)


#region notifications
@login_required(login_url='iniciar_sesion')
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    print('\n\nNotification ID:', notification_id)
    print('Notification Object:', notification)
    if request.method == 'POST' and notification:
        notification.is_read = True
        notification.save()     # mark as read
        
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

@login_required(login_url='iniciar_sesion')
def clear_notifications(request):
    if request.method == 'POST':
        notifications = Notification.objects.filter(user=request.user)
        notifications.delete()
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

@login_required(login_url='iniciar_sesion')
def show_all_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'notifications': notifications,
    }
    return render(request, 'estudiante/panel-estudiante.html', context)
#endregion


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def user_management(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])    # hash the password before saving
            user.save()
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('user_management')
        else:
            messages.error(request, 'Error al crear el usuario.')
    
    users = CustomUser.objects.all()
    context = {
        'users': users,
        'form': form,
    }
    return render(request, 'escuela/gestion-usuarios.html', context)

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'escuela/editar-usuario.html', {'form': form, 'user': user})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def toggle_lock_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    # Toggle the locked state
    user.is_locked = not user.is_locked
    if user.is_locked:
        user.locked_at = timezone.now()
        messages.success(request, f'User {user.email} locked.')
    else:
        user.locked_at = None
        messages.success(request, f'User {user.email} unlocked.')
    user.save()
    return redirect('user_management')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, 'Usuario eliminado correctamente.')
    return redirect('user_management')

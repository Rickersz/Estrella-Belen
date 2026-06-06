from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.urls import reverse
from autenticacion.models import AccessRequest, CustomUser
from autenticacion.email_queue import enqueue_generic_email
from .forms import InvitationPasswordForm, RepresentativeAccessForm, SchoolConfigurationForm, UserCreationForm, UserEditForm
from escuela import context_processors
from .models import AuditLog, Notification, RepresentativeInvitation, SchoolConfiguration
from .audit import log_audit
from estudiante.models import Parent, Student
from profesor.models import Teacher
from materia.models import Subject
from bitacora.models import AccessLog
from pagos.models import Payment
from escuela.models import ClassTeacherAssignment


def get_admin_dashboard_context(extra_context=None):
    context = {
        'active_academic_year': SchoolConfiguration.get_solo().active_academic_year,
        'students_count': Student.objects.filter(is_archived=False).count(),
        'teachers_count': Teacher.objects.count(),
        'subjects_count': Subject.objects.count(),
        'access_logs_count': AccessLog.objects.count(),
        'pending_payments_count': Payment.objects.filter(status__in=[Payment.STATUS_PENDING, Payment.STATUS_PARTIAL, Payment.STATUS_OVERDUE]).count(),
        'overdue_payments_count': Payment.objects.filter(status=Payment.STATUS_OVERDUE).count(),
        'payments_debt': Payment.objects.filter(balance__gt=0).aggregate(total=Sum('balance'))['total'] or 0,
        'recent_students': Student.objects.select_related('parent').filter(is_archived=False).order_by('-id')[:8],
        'recent_access_logs': AccessLog.objects.select_related('user').order_by('-created_at')[:8],
        'recent_payments': Payment.objects.select_related('student', 'representative').order_by('-updated_at')[:8],
    }
    if extra_context:
        context.update(extra_context)
    return context


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


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
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    return render(request, 'estudiante/panel-estudiante.html', {'notifications': notifications})

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_representative, login_url='iniciar_sesion')
def representative_dashboard(request):
    parent = getattr(request.user, 'representante', None)
    students = parent.student_set.filter(is_archived=False).order_by('first_name', 'last_name') if parent else Student.objects.none()
    selected_student = None
    if parent:
        selected_id = request.GET.get('student')
        selected_student = students.filter(pk=selected_id).first() if selected_id else students.first()

    payments = Payment.objects.filter(representative=parent).select_related('student') if parent else Payment.objects.none()
    if selected_student:
        payments = payments.filter(student=selected_student)
    return render(request, 'representante/panel-representante.html', {
        'parent': parent,
        'students': students,
        'selected_student': selected_student,
        'payments': payments[:8],
        'pending_payments': payments.filter(balance__gt=0),
        'debt': payments.filter(balance__gt=0).aggregate(total=Sum('balance'))['total'] or 0,
    })
#endregion


def create_notification(user, message):
    if user.is_authenticated:
        Notification.objects.create(user=user, message=message)        # create notification object in the database


def ensure_teacher_profile(user, previous_email=None):
    if not getattr(user, 'is_teacher', False):
        return None, False

    full_name = user.get_full_name() or user.email.split('@')[0]
    lookup_email = previous_email or user.email
    teacher = Teacher.objects.filter(email__iexact=lookup_email).first()
    created = False

    if teacher and teacher.email.lower() != user.email.lower():
        email_in_use = Teacher.objects.filter(email__iexact=user.email).exclude(pk=teacher.pk).exists()
        if not email_in_use:
            teacher.email = user.email

    if not teacher:
        teacher, created = Teacher.objects.get_or_create(
            email=user.email,
            defaults={
                'teacher_id': f'DOC-{user.pk:04d}',
                'name': full_name,
                'gender': 'Others',
                'date_of_birth': timezone.localdate().replace(year=timezone.localdate().year - 25),
                'joining_date': timezone.localdate(),
                'mobile_number': '0000000',
                'qualification': 'Por completar',
                'experience': 'Por completar',
                'address': 'Por completar',
                'city': 'Por completar',
                'state': 'Por completar',
                'country': 'Venezuela',
                'zip_code': '0000',
                'department': 'Por asignar',
            },
        )

    changed_fields = []
    if not teacher.name or teacher.name == 'Por completar':
        teacher.name = full_name
        changed_fields.append('name')
    if teacher.is_archived:
        teacher.is_archived = False
        changed_fields.append('is_archived')
    if teacher.email != user.email and not Teacher.objects.filter(email__iexact=user.email).exclude(pk=teacher.pk).exists():
        teacher.email = user.email
        changed_fields.append('email')
    if changed_fields:
        teacher.save(update_fields=changed_fields)
    return teacher, created
    
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
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
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
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])    # hash the password before saving
                user.save()
                teacher, teacher_created = ensure_teacher_profile(user)
            if teacher:
                estado_perfil = 'creado' if teacher_created else 'vinculado'
                messages.success(request, f'Usuario profesor creado correctamente. Perfil docente {estado_perfil}: {teacher.teacher_id}.')
            else:
                messages.success(request, 'Usuario creado correctamente.')
            return redirect('user_management')
        else:
            messages.error(request, 'Error al crear el usuario.')
    
    users = CustomUser.objects.filter(is_active=True)
    context = {
        'users': users,
        'form': form,
    }
    return render(request, 'escuela/gestion-usuarios.html', context)


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def system_configuration(request):
    config = SchoolConfiguration.get_solo()
    form = SchoolConfigurationForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        config = form.save()
        log_audit(request, 'actualizar_configuracion', config, 'Actualizo la configuracion general del sistema.')
        messages.success(request, 'Configuracion general actualizada correctamente.')
        return redirect('system_configuration')
    return render(request, 'escuela/configuracion.html', {'form': form, 'config': config})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def representative_management(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('estado', '').strip()
    parents = Parent.objects.select_related('user').prefetch_related('student_set', 'portal_invitations').annotate(students_count=Count('student'))
    if query:
        parents = parents.filter(
            Q(father_name__icontains=query) |
            Q(mother_name__icontains=query) |
            Q(father_email__icontains=query) |
            Q(mother_email__icontains=query) |
            Q(cedula_padre__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__student_id__icontains=query)
        ).distinct()
    if status == 'sin_usuario':
        parents = parents.filter(user__isnull=True)
    elif status == 'activo':
        parents = parents.filter(user__isnull=False, user__is_active=True, user__is_locked=False)
    elif status == 'bloqueado':
        parents = parents.filter(user__is_locked=True)
    elif status == 'invitado':
        parents = parents.filter(portal_invitations__status=RepresentativeInvitation.STATUS_PENDING).distinct()

    all_parents = Parent.objects.select_related('user')
    return render(request, 'escuela/representantes.html', {
        'parents': parents.order_by('father_name', 'mother_name'),
        'query': query,
        'status': status,
        'total_parents': all_parents.count(),
        'with_user': all_parents.filter(user__isnull=False).count(),
        'without_user': all_parents.filter(user__isnull=True).count(),
        'pending_invitations': RepresentativeInvitation.objects.filter(status=RepresentativeInvitation.STATUS_PENDING).count(),
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def access_request_list(request):
    status = request.GET.get('estado', '').strip()
    query = request.GET.get('q', '').strip()
    requests_qs = AccessRequest.objects.select_related('reviewed_by')
    if status:
        requests_qs = requests_qs.filter(status=status)
    if query:
        requests_qs = requests_qs.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(document_id__icontains=query) |
            Q(student_name__icontains=query)
        )
    return render(request, 'escuela/solicitudes-acceso.html', {
        'requests_qs': requests_qs,
        'status': status,
        'query': query,
        'status_choices': AccessRequest.STATUS_CHOICES,
        'pending_count': AccessRequest.objects.filter(status=AccessRequest.STATUS_PENDING).count(),
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def update_access_request_status(request, request_id, status):
    access_request = get_object_or_404(AccessRequest, pk=request_id)
    valid_statuses = {choice[0] for choice in AccessRequest.STATUS_CHOICES}
    if status not in valid_statuses:
        messages.error(request, 'Estado de solicitud invalido.')
        return redirect('access_request_list')
    access_request.status = status
    access_request.reviewed_by = request.user
    access_request.reviewed_at = timezone.now()
    access_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
    log_audit(request, 'actualizar_solicitud_acceso', access_request, f'Cambio solicitud a {status}.')
    messages.success(request, 'Solicitud actualizada correctamente.')
    return redirect('access_request_list')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@ensure_csrf_cookie
def representative_access(request, parent_id):
    parent = get_object_or_404(Parent.objects.select_related('user'), pk=parent_id)
    form = RepresentativeAccessForm(request.POST or None, parent=parent)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower()
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'is_representative': True,
                'is_active': False,
            },
        )
        if created:
            user.set_unusable_password()
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.is_representative = True
        user.save()
        parent.user = user
        parent.save(update_fields=['user'])
        invitation = create_representative_invitation(request, parent, user, email)
        send_representative_invitation(request, invitation)
        log_audit(request, 'crear_acceso_representante', parent, f'Creo acceso e invitacion para {email}.')
        messages.success(request, 'Acceso creado. Se envio la invitacion al correo del representante.')
        return redirect('representative_management')
    return render(request, 'escuela/acceso-representante.html', {'form': form, 'parent': parent})


def create_representative_invitation(request, parent, user, email):
    RepresentativeInvitation.objects.filter(
        parent=parent,
        user=user,
        status=RepresentativeInvitation.STATUS_PENDING,
    ).update(status=RepresentativeInvitation.STATUS_CANCELLED)
    return RepresentativeInvitation.objects.create(
        parent=parent,
        user=user,
        email=email,
        created_by=request.user,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )


def send_representative_invitation(request, invitation):
    invitation_url = request.build_absolute_uri(reverse('accept_representative_invitation', args=[invitation.token]))
    message = (
        'Hola.\n\n'
        'La institucion creo tu acceso al Portal de Padres.\n\n'
        f'Ingresa en este enlace para crear tu contraseña:\n{invitation_url}\n\n'
        'El enlace vence en 7 dias. Si no esperabas este correo, puedes ignorarlo.'
    )
    enqueue_generic_email('Invitacion al Portal de Padres - Estrella de Belen', message, invitation.email)


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def resend_representative_invitation(request, parent_id):
    parent = get_object_or_404(Parent.objects.select_related('user'), pk=parent_id, user__isnull=False)
    invitation = create_representative_invitation(request, parent, parent.user, parent.user.email)
    send_representative_invitation(request, invitation)
    log_audit(request, 'reenviar_invitacion_representante', parent, f'Reenvio invitacion a {parent.user.email}.')
    messages.success(request, 'Invitacion reenviada correctamente.')
    return redirect('representative_management')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def toggle_representative_access(request, parent_id):
    parent = get_object_or_404(Parent.objects.select_related('user'), pk=parent_id, user__isnull=False)
    user = parent.user
    user.is_locked = not user.is_locked
    user.locked_at = timezone.now() if user.is_locked else None
    user.save(update_fields=['is_locked', 'locked_at'])
    action = 'bloqueo_acceso_representante' if user.is_locked else 'desbloqueo_acceso_representante'
    log_audit(request, action, parent, f'Cambio acceso de {user.email}.')
    messages.success(request, 'Estado de acceso actualizado.')
    return redirect('representative_management')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def unlink_representative_access(request, parent_id):
    parent = get_object_or_404(Parent.objects.select_related('user'), pk=parent_id, user__isnull=False)
    email = parent.user.email
    RepresentativeInvitation.objects.filter(parent=parent, status=RepresentativeInvitation.STATUS_PENDING).update(status=RepresentativeInvitation.STATUS_CANCELLED)
    parent.user = None
    parent.save(update_fields=['user'])
    log_audit(request, 'desvincular_representante', parent, f'Desvinculo acceso {email}.')
    messages.warning(request, 'Acceso desvinculado del representante.')
    return redirect('representative_management')


@ensure_csrf_cookie
def accept_representative_invitation(request, token):
    invitation = get_object_or_404(RepresentativeInvitation.objects.select_related('user', 'parent'), token=token)
    invitation.mark_expired_if_needed()
    if not invitation.is_valid:
        return render(request, 'escuela/invitacion-expirada.html', {'invitation': invitation})
    form = InvitationPasswordForm(request.POST or None, user=invitation.user)
    if request.method == 'POST' and form.is_valid():
        user = invitation.user
        user.set_password(form.cleaned_data['password'])
        user.is_active = True
        user.is_representative = True
        user.is_locked = False
        user.locked_at = None
        user.save(update_fields=['password', 'is_active', 'is_representative', 'is_locked', 'locked_at'])
        invitation.status = RepresentativeInvitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=['status', 'accepted_at'])
        login(request, user, backend='autenticacion.backends.EmailBackend')
        messages.success(request, 'Tu acceso al Portal de Padres fue activado correctamente.')
        return redirect('representative_dashboard')
    return render(request, 'escuela/aceptar-invitacion.html', {'form': form, 'invitation': invitation})

@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    previous_email = user.email
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            teacher, teacher_created = ensure_teacher_profile(user, previous_email=previous_email)
            if teacher:
                estado_perfil = 'creado' if teacher_created else 'vinculado'
                messages.success(request, f'Usuario actualizado correctamente. Perfil docente {estado_perfil}.')
            else:
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
        messages.success(request, f'Usuario {user.email} bloqueado.')
    else:
        user.locked_at = None
        messages.success(request, f'Usuario {user.email} desbloqueado.')
    user.save()
    return redirect('user_management')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.is_locked = True
    user.locked_at = timezone.now()
    user.save(update_fields=['is_active', 'is_locked', 'locked_at'])
    log_audit(request, 'desactivar_usuario', user, f'Desactivo usuario {user.email}.')
    messages.success(request, 'Usuario desactivado correctamente.')
    return redirect('user_management')


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def deactivated_users(request):
    users = CustomUser.objects.filter(is_active=False).order_by('email')
    return render(request, 'escuela/usuarios-desactivados.html', {'users': users})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
@require_POST
def restore_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_active=False)
    user.is_active = True
    user.is_locked = False
    user.locked_at = None
    user.failed_login_attempts = 0
    user.save(update_fields=['is_active', 'is_locked', 'locked_at', 'failed_login_attempts'])
    log_audit(request, 'restaurar_usuario', user, f'Restauro usuario {user.email}.')
    messages.success(request, 'Usuario restaurado correctamente.')
    return redirect('deactivated_users')

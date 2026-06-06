from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test

from escuela.audit import log_audit
from escuela.models import ClassTeacherAssignment
from .forms import TeacherForm
from .models import Teacher


def puede_ver_profesores(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False))


def puede_gestionar_profesores(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


def agregar_errores_formulario(request, form):
    for field, errors in form.errors.items():
        label = form.fields[field].label if field in form.fields else 'Formulario'
        for error in errors:
            messages.error(request, f'{label}: {error}')


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_profesores, login_url='iniciar_sesion')
def add_teacher(request):
    if request.method == 'POST':
        data = request.POST.copy()
        if 'teacher_name' in data and 'name' not in data:
            data['name'] = data.get('teacher_name')
        form = TeacherForm(data, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor agregado correctamente.')
            return redirect('teacher_list')
        agregar_errores_formulario(request, form)
        messages.error(request, 'Revisa los datos ingresados e inténtalo nuevamente.')
    return render(request, 'profesor/agregar-profesor.html')


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_profesores, login_url='iniciar_sesion')
def teacher_list(request):
    teachers = Teacher.objects.filter(is_archived=False)
    return render(request, 'profesor/lista-profesores.html', {'teachers': teachers})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_profesores, login_url='iniciar_sesion')
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id, is_archived=False)
    assignments = ClassTeacherAssignment.objects.select_related('class_assigned', 'subject').filter(teacher=teacher)
    return render(request, 'profesor/detalle-profesor.html', {'teacher': teacher, 'assignments': assignments})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_profesores, login_url='iniciar_sesion')
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id, is_archived=False)
    if request.method == 'POST':
        data = request.POST.copy()
        if 'teacher_name' in data and 'name' not in data:
            data['name'] = data.get('teacher_name')
        form = TeacherForm(data, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor actualizado correctamente.')
            return redirect('teacher_list')
        agregar_errores_formulario(request, form)
        messages.error(request, 'Revisa los datos ingresados e inténtalo nuevamente.')
    return render(request, 'profesor/editar-profesor.html', {'teacher': teacher})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_profesores, login_url='iniciar_sesion')
def delete_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, teacher_id=teacher_id, is_archived=False)
        teacher_name = teacher.name
        teacher.is_archived = True
        teacher.save(update_fields=['is_archived'])
        ClassTeacherAssignment.objects.filter(teacher=teacher, is_active=True).update(is_active=False)
        log_audit(request, 'archivar_profesor', teacher, f'Archivo profesor {teacher}.')
        messages.success(request, f'{teacher_name} archivado correctamente.')
        return redirect('teacher_list')
    return HttpResponseForbidden('No se puede eliminar el profesor')


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_profesores, login_url='iniciar_sesion')
def archived_teachers(request):
    teachers = Teacher.objects.filter(is_archived=True).order_by('name')
    return render(request, 'profesor/archivados.html', {'teachers': teachers})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_profesores, login_url='iniciar_sesion')
def restore_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, teacher_id=teacher_id, is_archived=True)
        teacher.is_archived = False
        teacher.save(update_fields=['is_archived'])
        log_audit(request, 'restaurar_profesor', teacher, f'Restauro profesor {teacher}.')
        messages.success(request, 'Profesor restaurado correctamente.')
        return redirect('archived_teachers')
    return HttpResponseForbidden('No se puede restaurar el profesor')

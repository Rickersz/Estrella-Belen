from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction, IntegrityError

from escuela.audit import log_audit
from escuela.models import ClassTeacherAssignment
from .forms import AssignmentForm, SubjectForm
from .models import Subject


def puede_ver_materias(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False))


def puede_gestionar_materias(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def add_subject(request):
    form = SubjectForm()
    if request.method == 'POST':
        data = request.POST.copy()
        if 'subject_code' in data and 'code' not in data:
            data['code'] = data.get('subject_code')
        if 'subject_name' in data and 'name' not in data:
            data['name'] = data.get('subject_name')
        form = SubjectForm(data)
        if not form.is_valid():
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else 'Formulario'
                for error in errors:
                    messages.error(request, f'{label}: {error}')
            return render(request, 'materia/agregar-materia.html', {'form': form})

        form.save()
        messages.success(request, 'Materia agregada correctamente.')
        return redirect('subject_list')

    return render(request, 'materia/agregar-materia.html', {'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_materias, login_url='iniciar_sesion')
def subject_list(request):
    subjects = Subject.objects.filter(is_archived=False)
    return render(request, 'materia/lista-materias.html', {'subjects': subjects})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def edit_subject(request, code):
    subject = get_object_or_404(Subject, code=code, is_archived=False)
    form = SubjectForm(instance=subject)

    if request.method == 'POST':
        data = request.POST.copy()
        if 'subject_code' in data and 'code' not in data:
            data['code'] = data.get('subject_code')
        if 'subject_name' in data and 'name' not in data:
            data['name'] = data.get('subject_name')
        form = SubjectForm(data, instance=subject)
        if not form.is_valid():
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else 'Formulario'
                for error in errors:
                    messages.error(request, f'{label}: {error}')
            return render(request, 'materia/editar-materia.html', {'subject': subject, 'form': form})

        form.save()
        messages.success(request, 'Materia actualizada correctamente.')
        return redirect('subject_list')

    return render(request, 'materia/editar-materia.html', {'subject': subject, 'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def delete_subject(request, code):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, code=code, is_archived=False)
        subject_name = f'{subject.code} - {subject.name}'
        subject.is_archived = True
        subject.save(update_fields=['is_archived'])
        ClassTeacherAssignment.objects.filter(subject=subject, is_active=True).update(is_active=False)
        log_audit(request, 'archivar_materia', subject, f'Archivo materia {subject}.')
        messages.success(request, f'{subject_name} archivada correctamente.')
        return redirect('subject_list')
    return HttpResponseForbidden('No se puede eliminar la materia')


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def archived_subjects(request):
    subjects = Subject.objects.filter(is_archived=True).order_by('code')
    return render(request, 'materia/archivadas.html', {'subjects': subjects})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def restore_subject(request, code):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, code=code, is_archived=True)
        subject.is_archived = False
        subject.save(update_fields=['is_archived'])
        log_audit(request, 'restaurar_materia', subject, f'Restauro materia {subject}.')
        messages.success(request, 'Materia restaurada correctamente.')
        return redirect('archived_subjects')
    return HttpResponseForbidden('No se puede restaurar la materia')


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_materias, login_url='iniciar_sesion')
def assignment_list(request):
    assignments = ClassTeacherAssignment.objects.select_related('class_assigned', 'subject', 'teacher').filter(
        subject__is_archived=False,
        teacher__is_archived=False,
    )
    return render(request, 'materia/lista-asignaciones.html', {'assignments': assignments})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def add_assignment(request):
    form = AssignmentForm()
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Asignación agregada correctamente.')
                    return redirect('assignment_list')
            except IntegrityError:
                messages.error(request, 'Esta asignación ya existe.')
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    return render(request, 'materia/agregar-asignacion.html', {'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def edit_assignment(request, assignment_id):
    obj = get_object_or_404(ClassTeacherAssignment, id=assignment_id)
    form = AssignmentForm(instance=obj)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Asignación actualizada correctamente.')
                    return redirect('assignment_list')
            except IntegrityError:
                messages.error(request, 'Esta asignación ya existe.')
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    return render(request, 'materia/editar-asignacion.html', {'form': form, 'assignment': obj})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_materias, login_url='iniciar_sesion')
def delete_assignment(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(ClassTeacherAssignment, id=assignment_id)
        assignment.is_active = False
        assignment.save(update_fields=['is_active'])
        log_audit(request, 'desactivar_asignacion', assignment, f'Desactivo asignacion {assignment}.')
        messages.success(request, 'Asignacion desactivada correctamente.')
        return redirect('assignment_list')
    return HttpResponseForbidden('No se puede eliminar la asignación')


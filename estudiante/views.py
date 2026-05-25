from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
import csv

from .forms import EnrollmentForm, ParentForm, StudentForm
from .models import Student, Parent, Enrollment
from escuela.views import create_notification
from reportes.models import Constancia


def puede_ver_estudiantes(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False) or getattr(user, 'is_student', False))


def puede_gestionar_estudiantes(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False))


def puede_eliminar_estudiantes(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


def agregar_errores_formulario(request, *forms):
    for form in forms:
        for field, errors in form.errors.items():
            label = form.fields[field].label if field in form.fields else 'Formulario'
            for error in errors:
                messages.error(request, f'{label}: {error}')


# =========================
# ADD STUDENT + ENROLLMENT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def add_student(request):
    if request.method == 'POST':
        student_form = StudentForm(request.POST, request.FILES)
        parent_form = ParentForm(request.POST)
        enrollment_form = EnrollmentForm(request.POST)

        if student_form.is_valid() and parent_form.is_valid() and enrollment_form.is_valid():
            with transaction.atomic():
                parent = parent_form.save()
                student = student_form.save(commit=False)
                student.parent = parent
                student.save()
                Enrollment.objects.create(
                    student=student,
                    academic_year='2025-2026',
                    etapa=student.etapa,
                    grado=student.grado,
                    section=student.section,
                    monto_inscripcion=enrollment_form.cleaned_data['monto_inscripcion'],
                )
            messages.success(request, 'Estudiante inscrito correctamente.')
            create_notification(request.user, f'Estudiante {student.first_name} {student.last_name} inscrito.')
            return redirect('constancia_inscripcion', slug=student.slug)

        agregar_errores_formulario(request, student_form, parent_form, enrollment_form)
        messages.error(request, 'Revisa los datos ingresados e intÃ©ntalo nuevamente.')

    return render(request, "estudiante/agregar-estudiante.html")


# =========================
# STUDENT LIST
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_estudiantes, login_url='iniciar_sesion')
def student_list(request):
    students = Student.objects.select_related('parent').all()
     # ðŸ”Ž SEARCH
    query = request.GET.get('q')
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(student_id__icontains=query)
        )

    # ðŸŽ¯ FILTERS
    etapa = request.GET.get('etapa')
    grado = request.GET.get('grado')

    if etapa:
        students = students.filter(etapa=etapa)

    if grado:
        students = students.filter(grado=grado)

    return render(request, 'estudiante/lista-estudiantes.html', {
        'students': students,
    })

# =========================
# STUDENT DETAIL
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_estudiantes, login_url='iniciar_sesion')
def student_detail(request, slug):
    student = get_object_or_404(Student.objects.select_related('parent'), slug=slug)
    return render(request, 'estudiante/detalle-estudiante.html', {'student': student})


# =========================
# EDIT STUDENT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def edit_student(request, slug):
    student = get_object_or_404(Student.objects.select_related('parent'), slug=slug)
    parent = student.parent

    if request.method == 'POST':
        student_form = StudentForm(request.POST, request.FILES, instance=student)
        parent_form = ParentForm(request.POST, instance=parent)

        if student_form.is_valid() and parent_form.is_valid():
            with transaction.atomic():
                parent = parent_form.save()
                student = student_form.save(commit=False)
                student.parent = parent
                student.save()
            messages.success(request, 'Estudiante actualizado correctamente.')
            create_notification(request.user, f'Estudiante {student.first_name} {student.last_name} actualizado.')
            return redirect('student_list')

        agregar_errores_formulario(request, student_form, parent_form)
        messages.error(request, 'Revisa los datos ingresados e intentalo nuevamente.')
    else:
        student_form = StudentForm(instance=student)
        parent_form = ParentForm(instance=parent)

    return render(request, 'estudiante/editar-estudiante.html', {
        'student': student,
        'parent': parent,
        'student_form': student_form,
        'parent_form': parent_form,
    })

# =========================
# DELETE STUDENT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_eliminar_estudiantes, login_url='iniciar_sesion')
def delete_student(request, slug):
    if request.method == 'POST':
        student = get_object_or_404(Student, slug=slug)
        student.delete()
        messages.success(request, 'Estudiante eliminado correctamente.')
        return redirect('student_list')

    return HttpResponseForbidden()


# =========================
# CSV EXPORT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def download_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estudiantes.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'CÃ©dula escolar', 'Nombres', 'Apellidos',
        'Etapa', 'Grado', 'SecciÃ³n',
        'GÃ©nero', 'Fecha de nacimiento', 'NÃºmero de admisiÃ³n'
    ])

    for student in Student.objects.all():
        writer.writerow([
            student.student_id,
            student.first_name,
            student.last_name,
            student.etapa,
            student.grado,
            student.section,
            student.gender,
            student.date_of_birth,
            student.admission_number,
        ])

    return response


# =========================
# CONSTANCIA DE INSCRIPCIÃ“N
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_estudiantes, login_url='iniciar_sesion')
def constancia_inscripcion(request, slug):
    student = get_object_or_404(Student.objects.select_related('parent'), slug=slug)
    enrollment = Enrollment.objects.filter(student=student).order_by('-date_enrolled').first()
    constancia = Constancia.objects.create(
        report_type=Constancia.TIPO_INSCRIPCION,
        student=student,
        issued_by=request.user,
        academic_year=enrollment.academic_year if enrollment else '2025-2026',
        amount_paid=enrollment.monto_inscripcion if enrollment else None,
    )
    return redirect('constancia_detail', pk=constancia.pk)

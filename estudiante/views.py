from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Q
import csv

from .forms import AttendanceRecordForm, EnrollmentForm, GradeSectionCapacityForm, ParentForm, SchoolYearClosureForm, StudentDocumentChecklistForm, StudentForm, StudentHealthRecordForm
from .models import AttendanceRecord, Enrollment, GradeSectionCapacity, Parent, Student, StudentDocumentChecklist, StudentHealthRecord
from escuela.views import create_notification
from escuela.models import ClassTeacherAssignment, SchoolConfiguration
from escuela.audit import log_audit
from profesor.models import Teacher
from reportes.models import Constancia
from reportes.views import datos_institucionales
from academico.models import AcademicGrade


def puede_ver_estudiantes(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False) or getattr(user, 'is_representative', False))


def puede_gestionar_estudiantes(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False))


def puede_eliminar_estudiantes(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


def puede_gestion_escolar(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


GRADE_FLOW = {
    ('Preescolar', '1er'): ('Preescolar', '2do'),
    ('Preescolar', '2do'): ('Preescolar', '3er'),
    ('Preescolar', '3er'): ('Primaria', '1ro'),
    ('Primaria', '1ro'): ('Primaria', '2do'),
    ('Primaria', '2do'): ('Primaria', '3ro'),
    ('Primaria', '3ro'): ('Primaria', '4to'),
    ('Primaria', '4to'): ('Primaria', '5to'),
    ('Primaria', '5to'): ('Primaria', '6to'),
}


def next_grade_for(student):
    return GRADE_FLOW.get((student.etapa, student.grado))


def agregar_errores_formulario(request, *forms):
    for form in forms:
        for field, errors in form.errors.items():
            label = form.fields[field].label if field in form.fields else 'Formulario'
            for error in errors:
                messages.error(request, f'{label}: {error}')


def secciones_asignadas_profesor(user):
    teacher = Teacher.objects.filter(email__iexact=user.email).first()
    if not teacher:
        return []
    return list(
        ClassTeacherAssignment.objects.filter(teacher=teacher, is_active=True)
        .values_list('class_assigned__section', flat=True)
        .distinct()
    )


def filtrar_estudiantes_por_rol(user, queryset):
    queryset = queryset.filter(is_archived=False)
    if getattr(user, 'is_admin', False):
        return queryset
    if getattr(user, 'is_teacher', False):
        sections = secciones_asignadas_profesor(user)
        return queryset.filter(section__in=sections) if sections else queryset.none()
    if getattr(user, 'is_representative', False):
        parent = getattr(user, 'representante', None)
        return queryset.filter(parent=parent) if parent else queryset.none()
    return queryset.none()


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
                config = SchoolConfiguration.get_solo()
                Enrollment.objects.create(
                    student=student,
                    academic_year=config.active_academic_year,
                    etapa=student.etapa,
                    grado=student.grado,
                    section=student.section,
                    monto_inscripcion=enrollment_form.cleaned_data['monto_inscripcion'],
                )
            messages.success(request, 'Estudiante inscrito correctamente.')
            create_notification(request.user, f'Estudiante {student.first_name} {student.last_name} inscrito.')
            return redirect('constancia_inscripcion', slug=student.slug)

        agregar_errores_formulario(request, student_form, parent_form, enrollment_form)
        messages.error(request, 'Revisa los datos ingresados e intentalo nuevamente.')

    return render(request, "estudiante/agregar-estudiante.html")


# =========================
# STUDENT LIST
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_estudiantes, login_url='iniciar_sesion')
def student_list(request):
    students = filtrar_estudiantes_por_rol(request.user, Student.objects.select_related('parent').all())
    # SEARCH
    query = request.GET.get('q')
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(student_id__icontains=query)
        )

    # FILTERS
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
    student = get_object_or_404(filtrar_estudiantes_por_rol(request.user, Student.objects.select_related('parent')), slug=slug)
    enrollments = student.enrollment_set.all()
    documents = getattr(student, 'documents', None)
    health_record = getattr(student, 'health_record', None)
    attendance = student.attendance_records.all()[:10]
    return render(request, 'estudiante/detalle-estudiante.html', {
        'student': student,
        'enrollments': enrollments,
        'documents': documents,
        'health_record': health_record,
        'attendance': attendance,
    })


# =========================
# EDIT STUDENT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def edit_student(request, slug):
    student = get_object_or_404(filtrar_estudiantes_por_rol(request.user, Student.objects.select_related('parent')), slug=slug)
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
        student.is_archived = True
        student.save(update_fields=['is_archived'])
        log_audit(request, 'archivar_estudiante', student, f'Archivo estudiante {student}.')
        messages.success(request, 'Estudiante archivado correctamente.')
        return redirect('student_list')

    return HttpResponseForbidden()


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_eliminar_estudiantes, login_url='iniciar_sesion')
def archived_students(request):
    students = Student.objects.select_related('parent').filter(is_archived=True).order_by('last_name', 'first_name')
    return render(request, 'estudiante/archivados.html', {'students': students})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_eliminar_estudiantes, login_url='iniciar_sesion')
def restore_student(request, slug):
    if request.method == 'POST':
        student = get_object_or_404(Student, slug=slug, is_archived=True)
        student.is_archived = False
        student.save(update_fields=['is_archived'])
        log_audit(request, 'restaurar_estudiante', student, f'Restauro estudiante {student}.')
        messages.success(request, 'Estudiante restaurado correctamente.')
        return redirect('archived_students')
    return HttpResponseForbidden()


# =========================
# CSV EXPORT
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def download_students_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="estudiantes.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Cedula escolar', 'Nombres', 'Apellidos',
        'Etapa', 'Grado', 'Seccion',
        'Genero', 'Fecha de nacimiento', 'Numero de admision'
    ])

    students = filtrar_estudiantes_por_rol(request.user, Student.objects.all())
    for student in students:
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
# CONSTANCIA DE INSCRIPCION
# =========================
@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_ver_estudiantes, login_url='iniciar_sesion')
def constancia_inscripcion(request, slug):
    student = get_object_or_404(filtrar_estudiantes_por_rol(request.user, Student.objects.select_related('parent')), slug=slug)
    enrollment = Enrollment.objects.filter(student=student).order_by('-date_enrolled').first()
    if request.method == 'POST':
        constancia = Constancia.objects.create(
            report_type=Constancia.TIPO_INSCRIPCION,
            student=student,
            issued_by=request.user,
            academic_year=enrollment.academic_year if enrollment else SchoolConfiguration.get_solo().active_academic_year,
            amount_paid=enrollment.monto_inscripcion if enrollment else None,
        )
        return redirect('constancia_detail', pk=constancia.pk)

    return render(request, 'estudiante/constancia-inscripcion.html', {
        'student': student,
        'parent': student.parent,
        'enrollment': enrollment,
        'institucion': datos_institucionales(),
        'active_academic_year': SchoolConfiguration.get_solo().active_academic_year,
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestion_escolar, login_url='iniciar_sesion')
def school_operations_dashboard(request):
    config = SchoolConfiguration.get_solo()
    enrollments = Enrollment.objects.filter(academic_year=config.active_academic_year)
    return render(request, 'estudiante/gestion-escolar.html', {
        'active_year': config.active_academic_year,
        'students_count': Student.objects.filter(is_archived=False).count(),
        'active_enrollments': enrollments.filter(result_status=Enrollment.STATUS_ACTIVE).count(),
        'without_documents': Student.objects.filter(is_archived=False, documents__isnull=True).count(),
        'attendance_absences': AttendanceRecord.objects.filter(academic_year=config.active_academic_year, status__in=[AttendanceRecord.STATUS_ABSENT, AttendanceRecord.STATUS_JUSTIFIED]).count(),
        'by_grade': enrollments.values('etapa', 'grado', 'section').annotate(total=Count('id')).order_by('etapa', 'grado', 'section'),
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestion_escolar, login_url='iniciar_sesion')
def capacity_list(request):
    capacities = GradeSectionCapacity.objects.all()
    form = GradeSectionCapacityForm(request.POST or None, initial={'academic_year': SchoolConfiguration.get_solo().active_academic_year})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cupo guardado correctamente.')
        return redirect('capacity_list')
    return render(request, 'estudiante/cupos.html', {'capacities': capacities, 'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def student_documents(request, slug):
    student = get_object_or_404(filtrar_estudiantes_por_rol(request.user, Student.objects.all()), slug=slug)
    record, _ = StudentDocumentChecklist.objects.get_or_create(student=student)
    form = StudentDocumentChecklistForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Documentos actualizados.')
        return redirect('student_detail', slug=student.slug)
    return render(request, 'estudiante/form-escolar.html', {'form': form, 'title': 'Documentos del estudiante', 'student': student})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def student_health(request, slug):
    student = get_object_or_404(filtrar_estudiantes_por_rol(request.user, Student.objects.all()), slug=slug)
    record, _ = StudentHealthRecord.objects.get_or_create(student=student)
    form = StudentHealthRecordForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ficha medica actualizada.')
        return redirect('student_detail', slug=student.slug)
    return render(request, 'estudiante/form-escolar.html', {'form': form, 'title': 'Ficha medica', 'student': student})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestionar_estudiantes, login_url='iniciar_sesion')
def attendance_list(request):
    config = SchoolConfiguration.get_solo()
    records = AttendanceRecord.objects.select_related('student', 'recorded_by').filter(academic_year=request.GET.get('ano') or config.active_academic_year)
    status = request.GET.get('estado', '')
    if status:
        records = records.filter(status=status)
    form = AttendanceRecordForm(request.POST or None, initial={'academic_year': config.active_academic_year})
    form.fields['student'].queryset = filtrar_estudiantes_por_rol(request.user, Student.objects.all())
    if request.method == 'POST' and form.is_valid():
        attendance = form.save(commit=False)
        attendance.recorded_by = request.user
        attendance.save()
        messages.success(request, 'Asistencia registrada.')
        return redirect('attendance_list')
    return render(request, 'estudiante/asistencia.html', {'records': records, 'form': form, 'status': status, 'status_choices': AttendanceRecord.STATUS_CHOICES})


@login_required(login_url='iniciar_sesion')
@user_passes_test(puede_gestion_escolar, login_url='iniciar_sesion')
def school_year_closure(request):
    config = SchoolConfiguration.get_solo()
    default_next = ''
    if '-' in config.active_academic_year:
        start, end = config.active_academic_year.split('-', 1)
        if start.isdigit() and end.isdigit():
            default_next = f'{int(start)+1}-{int(end)+1}'
    form = SchoolYearClosureForm(request.POST or None, initial={
        'current_academic_year': config.active_academic_year,
        'next_academic_year': default_next,
    })
    preview = Enrollment.objects.select_related('student').filter(academic_year=config.active_academic_year, result_status=Enrollment.STATUS_ACTIVE)
    if request.method == 'POST' and form.is_valid():
        current_year = form.cleaned_data['current_academic_year']
        next_year = form.cleaned_data['next_academic_year']
        default_section = form.cleaned_data['default_section']
        promoted = repeated = graduated = 0
        with transaction.atomic():
            enrollments = Enrollment.objects.select_related('student').filter(academic_year=current_year, result_status=Enrollment.STATUS_ACTIVE)
            for enrollment in enrollments:
                student = enrollment.student
                next_grade = next_grade_for(student)
                if not next_grade:
                    enrollment.result_status = Enrollment.STATUS_GRADUATED
                    enrollment.status = Enrollment.STATUS_GRADUATED
                    enrollment.next_academic_year = next_year
                    enrollment.save(update_fields=['result_status', 'status', 'next_academic_year'])
                    graduated += 1
                    continue
                target_etapa, target_grado = next_grade
                enrollment.result_status = Enrollment.STATUS_PROMOTED
                enrollment.status = Enrollment.STATUS_PROMOTED
                enrollment.next_academic_year = next_year
                enrollment.save(update_fields=['result_status', 'status', 'next_academic_year'])
                Student.objects.filter(pk=student.pk).update(etapa=target_etapa, grado=target_grado, section=default_section)
                Enrollment.objects.get_or_create(
                    student=student,
                    academic_year=next_year,
                    defaults={
                        'etapa': target_etapa,
                        'grado': target_grado,
                        'section': default_section,
                        'monto_inscripcion': 0,
                    },
                )
                promoted += 1
            if form.cleaned_data['close_grades']:
                AcademicGrade.objects.filter(academic_year=current_year).update(is_locked=True)
            config.active_academic_year = next_year
            config.save(update_fields=['active_academic_year', 'updated_at'])
        messages.success(request, f'Cierre completado. Promovidos: {promoted}. Egresados: {graduated}. Repite: {repeated}.')
        return redirect('school_operations_dashboard')
    return render(request, 'estudiante/cierre-anual.html', {'form': form, 'preview': preview})

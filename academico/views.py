from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from estudiante.models import Student
from reportes.models import Constancia
from .forms import AcademicGradeForm, AnnouncementForm, CommunicationMessageForm, DisciplineObservationForm, ScheduleForm, SchoolEventForm
from .models import AcademicGrade, Announcement, ClassSchedule, CommunicationMessage, DisciplineObservation, SchoolEvent
from .utils import can_manage_academic, is_admin, is_representative, notify_announcement, students_for_user, teacher_for_user, xlsx_response


def can_view_academic(user):
    return user.is_authenticated and (getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False) or getattr(user, 'is_representative', False))


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def academic_dashboard(request):
    students = students_for_user(request.user)
    grades = AcademicGrade.objects.filter(student__in=students)
    context = {
        'students_count': students.count(),
        'grades_count': grades.count(),
        'average_grade': grades.aggregate(avg=Avg('grade'))['avg'] or 0,
        'events_count': SchoolEvent.objects.count(),
        'recent_grades': grades.select_related('student', 'subject')[:8],
        'announcements': Announcement.objects.all()[:5],
    }
    return render(request, 'academico/dashboard.html', context)


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def grade_list(request):
    grades = AcademicGrade.objects.select_related('student', 'subject', 'teacher').filter(student__in=students_for_user(request.user))
    query = request.GET.get('q', '').strip()
    if query:
        grades = grades.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__student_id__icontains=query) |
            Q(subject__name__icontains=query)
        )
    page_obj = Paginator(grades, 20).get_page(request.GET.get('page'))
    return render(request, 'academico/notas.html', {'grades': page_obj, 'page_obj': page_obj, 'query': query})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_academic, login_url='iniciar_sesion')
def grade_create(request):
    form = AcademicGradeForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        grade = form.save(commit=False)
        grade.created_by = request.user
        if getattr(request.user, 'is_teacher', False) and not grade.teacher:
            grade.teacher = teacher_for_user(request.user)
        grade.save()
        messages.success(request, 'Nota guardada correctamente.')
        return redirect('grade_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Cargar nota'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_academic, login_url='iniciar_sesion')
def grade_edit(request, pk):
    grade = get_object_or_404(AcademicGrade.objects.filter(student__in=students_for_user(request.user)), pk=pk)
    if grade.is_locked and not is_admin(request.user):
        messages.error(request, 'Esta nota esta bloqueada y solo administracion puede modificarla.')
        return redirect('grade_list')
    form = AcademicGradeForm(request.POST or None, instance=grade, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Nota actualizada correctamente.')
        return redirect('grade_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Editar nota'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def academic_history(request, student_id=None):
    students = students_for_user(request.user)
    student = get_object_or_404(students, pk=student_id) if student_id else students.first()
    grades = AcademicGrade.objects.filter(student=student).select_related('subject', 'teacher') if student else AcademicGrade.objects.none()
    observations = DisciplineObservation.objects.filter(student=student) if student else DisciplineObservation.objects.none()
    return render(request, 'academico/historial.html', {'students': students, 'student': student, 'grades': grades, 'observations': observations})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def report_card_pdf(request, student_id):
    student = get_object_or_404(students_for_user(request.user), pk=student_id)
    grades = AcademicGrade.objects.filter(student=student).select_related('subject')
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    y = 10 * inch
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(inch, y, 'Boletin Academico')
    y -= 0.35 * inch
    pdf.setFont('Helvetica', 11)
    pdf.drawString(inch, y, f'Estudiante: {student.first_name} {student.last_name}')
    y -= 0.25 * inch
    pdf.drawString(inch, y, f'Grado/Seccion: {student.grado or "-"} / {student.section}')
    y -= 0.4 * inch
    pdf.setFont('Helvetica-Bold', 10)
    pdf.drawString(inch, y, 'Materia')
    pdf.drawString(3.6 * inch, y, 'Lapso')
    pdf.drawString(4.8 * inch, y, 'Nota')
    y -= 0.2 * inch
    pdf.setFont('Helvetica', 10)
    for grade in grades:
        pdf.drawString(inch, y, grade.subject.name)
        pdf.drawString(3.6 * inch, y, grade.get_period_display())
        pdf.drawString(4.8 * inch, y, str(grade.grade))
        y -= 0.22 * inch
        if y < inch:
            pdf.showPage()
            y = 10 * inch
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boletin_{student.student_id}.pdf"'
    return response


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def schedule_list(request):
    schedules = ClassSchedule.objects.select_related('class_assigned', 'subject', 'teacher')
    if not is_admin(request.user):
        sections = list(students_for_user(request.user).values_list('section', flat=True).distinct())
        schedules = schedules.filter(class_assigned__section__in=sections)
    return render(request, 'academico/horario.html', {'schedules': schedules})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def schedule_create(request):
    form = ScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Horario guardado.')
        return redirect('schedule_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Crear horario'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def calendar_list(request):
    events = SchoolEvent.objects.all()
    return render(request, 'academico/calendario.html', {'events': events})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def calendar_create(request):
    form = SchoolEventForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, 'Evento guardado.')
        return redirect('calendar_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Crear evento'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def observation_list(request):
    observations = DisciplineObservation.objects.select_related('student', 'teacher').filter(student__in=students_for_user(request.user))
    return render(request, 'academico/observaciones.html', {'observations': observations})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_academic, login_url='iniciar_sesion')
def observation_create(request):
    form = DisciplineObservationForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        observation = form.save(commit=False)
        observation.created_by = request.user
        observation.save()
        messages.success(request, 'Observacion registrada.')
        return redirect('observation_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Registrar observacion'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def announcement_list(request):
    announcements = Announcement.objects.all()
    return render(request, 'academico/anuncios.html', {'announcements': announcements})


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def announcement_create(request):
    form = AnnouncementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        announcement = form.save(commit=False)
        announcement.created_by = request.user
        announcement.save()
        notify_announcement(announcement)
        messages.success(request, 'Anuncio publicado.')
        return redirect('announcement_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Publicar anuncio'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def message_list(request):
    messages_qs = CommunicationMessage.objects.select_related('sender', 'recipient').filter(recipient=request.user)
    return render(request, 'academico/mensajes.html', {'messages_qs': messages_qs})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def message_create(request):
    form = CommunicationMessageForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.save()
        messages.success(request, 'Mensaje enviado.')
        return redirect('message_list')
    return render(request, 'academico/form.html', {'form': form, 'title': 'Nuevo mensaje'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def constancias_portal(request):
    students = students_for_user(request.user)
    return render(request, 'academico/constancias.html', {'students': students, 'tipos': Constancia.TIPO_CHOICES})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def academic_stats(request):
    grades = AcademicGrade.objects.filter(student__in=students_for_user(request.user))
    by_subject = grades.values('subject__name').annotate(avg=Avg('grade'), total=Count('id')).order_by('subject__name')
    by_period = grades.values('period').annotate(avg=Avg('grade'), total=Count('id')).order_by('period')
    return render(request, 'academico/estadisticas.html', {'by_subject': by_subject, 'by_period': by_period})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_academic, login_url='iniciar_sesion')
def export_grades_excel(request):
    grades = AcademicGrade.objects.select_related('student', 'subject').filter(student__in=students_for_user(request.user))
    rows = [
        [g.student.student_id, f'{g.student.first_name} {g.student.last_name}', g.subject.name, g.get_period_display(), g.grade, g.academic_year]
        for g in grades
    ]
    return xlsx_response('notas.xlsx', ['Cedula escolar', 'Estudiante', 'Materia', 'Lapso', 'Nota', 'Ano escolar'], rows)

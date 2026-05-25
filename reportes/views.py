from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Constancia
from .forms import ConstanciaForm
from django.template.loader import render_to_string
from django.http import HttpResponse
from estudiante.models import Student, Enrollment


def can_manage_constancias(user):
    return (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_teacher') and user.is_teacher)


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_constancias, login_url='iniciar_sesion')
def reportes_home(request):
    # Búsqueda de estudiante
    query = request.GET.get('q', '')
    students = Student.objects.all()
    if query:
        students = students.filter(first_name__icontains=query) | \
                   students.filter(last_name__icontains=query) | \
                   students.filter(student_id__icontains=query)

    # Obtener la última matrícula de cada estudiante
    estudiantes_con_matricula = []
    for student in students:
        enrollment = Enrollment.objects.filter(student=student).order_by('-date_enrolled').first()
        estudiantes_con_matricula.append({
            'student': student,
            'enrollment': enrollment,
        })

    return render(request, 'reportes/index.html', {
        'estudiantes_con_matricula': estudiantes_con_matricula,
        'query': query,
        'total': students.count(),
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_constancias, login_url='iniciar_sesion')
def constancia_create(request):
    if request.method == 'POST':
        form = ConstanciaForm(request.POST)
        if form.is_valid():
            const = form.save(commit=False)
            const.issued_by = request.user
            const.save()
            return redirect('reportes_home')
    else:
        form = ConstanciaForm()
    return render(request, 'reportes/constancia_form.html', {'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_constancias, login_url='iniciar_sesion')
def constancia_detail(request, pk):
    const = get_object_or_404(Constancia, pk=pk)
    try:
        from xhtml2pdf import pisa
        html = render_to_string('reportes/constancia_pdf.html', {'const': const})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="constancia_{const.pk}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generando PDF', status=500)
        return response
    except Exception:
        return render(request, 'reportes/constancia_detail.html', {'const': const})

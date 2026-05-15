from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
import csv

from .models import Student, Parent, Enrollment
from school.views import create_notification


# =========================
# ADD STUDENT + ENROLLMENT
# =========================
@login_required(login_url='login')
def add_student(request):
    if request.method == 'POST':

        # STUDENT DATA
        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        tiene_cedula = request.POST.get("tiene_cedula") == "on"
        cedula = request.POST.get("cedula")

        etapa = request.POST.get("etapa")
        grado = request.POST.get("grado")
        section = request.POST.get('section')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        admission_number = request.POST.get('admission_number')
        joining_date = request.POST.get('joining_date')
        student_image = request.FILES.get('student_image')
        nacionalidad = request.POST.get('nacionalidad')
        estado_natal = request.POST.get('estado_natal')
        edad = request.POST.get('edad')
        etnia = request.POST.get('etnia')
        pais_extranjero = request.POST.get('pais_extranjero')
        direccion_completa = request.POST.get('direccion_completa')

        # TALLAS
        pantalon = request.POST.get('pantalon')
        camisa = request.POST.get('camisa')
        calzado = request.POST.get('calzado')
        peso = request.POST.get('peso')
        estatura = request.POST.get('estatura')
        transporte = request.POST.get('transporte')

        vive_con_padres = request.POST.get('vive_con_padres')
        huerfano = request.POST.get('huerfano')

        # SALUD
        discapacidad = request.POST.get('discapacidad')
        condicion = request.POST.get('condicion')
        area_condicion = request.POST.get('area_condicion')
        tipo_discapacidad = request.POST.get('tipo_discapacidad')
        carnet_discapacidad = request.POST.get('carnet_discapacidad')
        informe_medico = request.POST.get('informe_medico')
        recibe_tratamiento = request.POST.get('recibe_tratamiento')
        cual_tratamiento = request.POST.get('cual_tratamiento')

        # ESCOLARIDAD
        plantel_anterior = request.POST.get('plantel_anterior')
        repitiente = request.POST.get('repitiente')
        aula_integrada = request.POST.get('aula_integrada')
        cargado_sge = request.POST.get('cargado_sge')
        observaciones = request.POST.get('observaciones')


        # PARENT DATA
        parent = Parent.objects.create(

        father_name = request.POST.get('father_name'),
        father_mobile = request.POST.get('father_mobile'),
        father_email=request.POST.get('father_email'),

        mother_name=request.POST.get('mother_name'),
        mother_mobile=request.POST.get('mother_mobile'),
        mother_email=request.POST.get('mother_email'),

        cedula_padre=request.POST.get('cedula_padre'),
        fechan_padre=request.POST.get('fechan_padre'),
        trabaja_padre=request.POST.get('trabaja_padre'),
        lugar_trabajo_padre=request.POST.get('lugar_trabajo_padre'),

        fechan_madre=request.POST.get('fechan_madre'),
        trabaja_madre=request.POST.get('trabaja_madre'),
        lugar_trabajo_madre=request.POST.get('lugar_trabajo_madre'),

)


        # CREATE STUDENT
        student = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            tiene_cedula=tiene_cedula,
            cedula=cedula,
            etapa=etapa,
            grado=grado,
            section=section,
            gender=gender,
            date_of_birth=date_of_birth,
            admission_number=admission_number,
            joining_date=joining_date,
            student_image=student_image,
            parent=parent,
            nacionalidad=nacionalidad,
            estado_natal=estado_natal,
            edad=edad,
            etnia=etnia,
            pais_extranjero=pais_extranjero,
            direccion_completa=direccion_completa,

            pantalon=pantalon,
            camisa=camisa,
            calzado=calzado,
            peso=peso,
            estatura=estatura,
            transporte=transporte,

            vive_con_padres=vive_con_padres,
            huerfano=huerfano,

            discapacidad=discapacidad,
            condicion=condicion,
            area_condicion=area_condicion,
            tipo_discapacidad=tipo_discapacidad,
            carnet_discapacidad=carnet_discapacidad,
            informe_medico=informe_medico,
            recibe_tratamiento=recibe_tratamiento,
            cual_tratamiento=cual_tratamiento,

            plantel_anterior=plantel_anterior,
            repitiente=repitiente,
            aula_integrada=aula_integrada,
            cargado_sge=cargado_sge,
            observaciones=observaciones,
            
        )

        # CREATE ENROLLMENT
        Enrollment.objects.create(
            student=student,
            academic_year="2025-2026",
            etapa=etapa,
            grado=grado,
            section=section,
        )

        messages.success(request, "Student added successfully!")
        return redirect("student_list")

    return render(request, "student/add-student.html")


# =========================
# STUDENT LIST
# =========================
@login_required(login_url='login')
def student_list(request):
    students = Student.objects.all()
     # 🔎 SEARCH
    query = request.GET.get('q')
    if query:
        students = students.filter(
            first_name__icontains=query
        ) | students.filter(
            last_name__icontains=query
        ) | students.filter(
            student_id__icontains=query
        )

    # 🎯 FILTERS
    etapa = request.GET.get('etapa')
    grado = request.GET.get('grado')

    if etapa:
        students = students.filter(etapa=etapa)

    if grado:
        students = students.filter(grado=grado)

    return render(request, 'student/student-list.html', {
        'students': students,
    })

# =========================
# STUDENT DETAIL
# =========================
@login_required(login_url='login')
def student_detail(request, slug):
    student = get_object_or_404(Student, slug=slug)
    return render(request, 'student/student-detail.html', {'student': student})


# =========================
# EDIT STUDENT
# =========================
@login_required(login_url='login')
def edit_student(request, slug):
    student = get_object_or_404(Student, slug=slug)
    parent = student.parent if hasattr(student, 'parent') else None

    if request.method == 'POST':

        student.student_id = request.POST.get('student_id')
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')

        student.tiene_cedula = request.POST.get("tiene_cedula") == "on"
        student.cedula = request.POST.get("cedula")

        student.etapa = request.POST.get("etapa")
        student.grado = request.POST.get("grado")
        student.section = request.POST.get('section')
        student.gender = request.POST.get('gender')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.admission_number = request.POST.get('admission_number')
        student.joining_date = request.POST.get('joining_date')
        student.nacionalidad = request.POST.get('nacionalidad')
        student.estado_natal = request.POST.get('estado_natal')
        student.edad = request.POST.get('edad')
        student.etnia = request.POST.get('etnia')
        student.direccion_completa = request.POST.get('direccion_completa')

        student.peso = request.POST.get('peso')
        student.estatura = request.POST.get('estatura')
        student.transporte = request.POST.get('transporte')

        student.discapacidad = request.POST.get('discapacidad')
        student.condicion = request.POST.get('condicion')
        student.tipo_discapacidad = request.POST.get('tipo_discapacidad')

        student.plantel_anterior = request.POST.get('plantel_anterior')
        student.observaciones = request.POST.get('observaciones')


        if request.FILES.get('student_image'):
            student.student_image = request.FILES.get('student_image')

        student.save()

        # UPDATE PARENT
        parent.father_name = request.POST.get('father_name')
        parent.father_mobile = request.POST.get('father_mobile')
        parent.father_email = request.POST.get('father_email')

        parent.mother_name = request.POST.get('mother_name')
        parent.mother_mobile = request.POST.get('mother_mobile')
        parent.mother_email = request.POST.get('mother_email')


        parent.cedula_padre=request.POST.get('cedula_padre')
        parent.fechan_padre=request.POST.get('fechan_padre')
        parent.trabaja_padre=request.POST.get('trabaja_padre')
        parent.lugar_trabajo_padre=request.POST.get('lugar_trabajo_padre')

        parent.fechan_madre=request.POST.get('fechan_madre')
        parent.trabaja_madre=request.POST.get('trabaja_madre')
        parent.lugar_trabajo_madre=request.POST.get('lugar_trabajo_madre')

        parent.save()

        messages.success(request, "Student updated successfully!")
        create_notification(request.user, f"Student {student.first_name} updated")

        return redirect('student_list')

    return render(request, 'student/edit-student.html', {'student': student, 'parent': parent})


# =========================
# DELETE STUDENT
# =========================
@login_required(login_url='login')
def delete_student(request, slug):
    if request.method == 'POST':
        student = get_object_or_404(Student, slug=slug)
        student.delete()
        messages.success(request, "Student deleted successfully!")
        return redirect('student_list')

    return HttpResponseForbidden()


# =========================
# CSV EXPORT
# =========================
@login_required(login_url='login')
def download_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'First Name', 'Last Name',
        'Etapa', 'Grado', 'Section',
        'Gender', 'DOB', 'Admission Number'
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
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Teacher
from school.models import ClassTeacherAssignment
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def add_teacher(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        name = request.POST.get('teacher_name')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        joining_date = request.POST.get('joining_date')
        mobile_number = request.POST.get('mobile_number')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')

        Teacher.objects.create(
            teacher_id=teacher_id,
            name=name,
            gender=gender,
            date_of_birth=date_of_birth,
            joining_date=joining_date,
            mobile_number=mobile_number,
            qualification=qualification,
            experience=experience,
            email=email,
            address=address,
            city=city,
            state=state,
            country=country,
            zip_code=zip_code
        )

        messages.success(request, 'Teacher added successfully!')
        return redirect('teacher_list')
    
    return render(request, 'teacher/add-teacher.html')

@login_required(login_url='login')
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teacher/teacher-list.html', {'teachers': teachers})

@login_required(login_url='login')
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher.objects.select_related('department'),   # Optimized quyer: (just 1 additional query for department else N+1 queries if accessed in template) 
                                teacher_id=teacher_id)
    
    assignments = ClassTeacherAssignment.objects.select_related('class_assigned', 'subject').filter(teacher=teacher)

    return render(request, 'teacher/teacher-detail.html', {'teacher': teacher, 'assignments': assignments})

@login_required(login_url='login')
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        name = request.POST.get('teacher_name')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        joining_date = request.POST.get('joining_date')
        mobile_number = request.POST.get('mobile_number')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')

        # update teacher data
        teacher.teacher_id=teacher_id
        teacher.name=name
        teacher.gender=gender
        teacher.date_of_birth=date_of_birth
        teacher.joining_date=joining_date
        teacher.mobile_number=mobile_number
        teacher.qualification=qualification
        teacher.experience=experience
        teacher.email=email
        teacher.address=address
        teacher.city=city
        teacher.state=state
        teacher.country=country
        teacher.zip_code=zip_code
        teacher.save()

        messages.success(request, 'Teacher updated successfully!')        
        return redirect('teacher_list')
    return render(request, 'teacher/edit-teacher.html', {'teacher': teacher})

@login_required(login_url='login')
def delete_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, teacher_id=teacher_id)
        teacher.delete()
        messages.success(request, f'{teacher.name} deleted successfully!')
        return redirect('teacher_list')

    return HttpResponseForbidden('Cannot delete teacher')
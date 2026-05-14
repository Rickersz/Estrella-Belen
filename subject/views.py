from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Subject

@login_required(login_url='login')
def add_subject(request):
    if request.method == 'POST':
        code = request.POST.get('subject_code')
        name = request.POST.get('subject_name')
        class_level = request.POST.get('class_level')
        subject = Subject.objects.create(
            code=code,
            name=name,
            class_level=class_level
        )
        subject.save()
        messages.success(request, 'Subject added successfully!')
        return redirect('subject_list')
    
    return render(request, 'subject/add-subject.html')

@login_required(login_url='login')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'subject/subject-list.html', {'subjects': subjects})

@login_required(login_url='login')
def edit_subject(request, code):
    subject = get_object_or_404(Subject, code=code)

    if request.method == 'POST':
        code = request.POST.get('subject_code')
        name = request.POST.get('subject_name')
        class_level = request.POST.get('class_level')
        
        subject.code = code
        subject.name = name
        subject.class_level = class_level
        subject.save()

        messages.success(request, 'Subject updated successfully!')
        # create_notification(request.user, f'Subject {subject.code} {subject.name} updated.')
        
        return redirect('subject_list')
    
    return render(request, 'subject/edit-subject.html', {'subject': subject})

@login_required(login_url='login')
def delete_subject(request, code):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, code=code)
        subject_name = f'{subject.code} - {subject.name}'
        subject.delete()
        messages.success(request, f'{subject_name} deleted successfully!')
        return redirect('subject_list')
    return HttpResponseForbidden('Cannot delete subject')


from school.models import ClassTeacherAssignment

# Assignment Views
@login_required(login_url='login')
def assignment_list(request):
    assignments = ClassTeacherAssignment.objects.select_related('class_assigned', 'subject', 'teacher').all()

    return render(request, 'subject/assignment-list.html', {'assignments': assignments})    

from school.models import Class
from teacher.models import Teacher
from django.db import transaction, IntegrityError
from .forms import AssignmentForm

@login_required(login_url='login')
def add_assignment(request):
    form = AssignmentForm()
    # form.fields['class_assigned'].queryset = Class.objects.all()
    if request.method == 'POST':
        form = AssignmentForm(request.POST)    
        if form.is_valid():
            try:
                with transaction.atomic():   # atomic transaction to ensure data integrity
                    assignment = form.save()
                    messages.success(request, 'Assignment added successfully!')
                    return redirect('assignment_list')
            except IntegrityError:
                messages.error(request, 'This assignment already exists(race)!')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'subject/add-assignment.html', {'form': form})

@login_required(login_url='login')
def edit_assignment(request, assignment_id):
    obj = get_object_or_404(ClassTeacherAssignment, id=assignment_id)
    form = AssignmentForm(instance=obj)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=obj)    
        if form.is_valid():
            try:
                with transaction.atomic():   # atomic transaction to ensure data integrity
                    assignment = form.save()
                    messages.success(request, 'Assignment updated successfully!')
                    return redirect('assignment_list')
            except IntegrityError:
                messages.error(request, 'This assignment already exists(race)!')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'subject/edit-assignment.html', {'form': form, 'assignment': obj})



# @login_required(login_url='login')
# def edit_assignment(request, assignment_id):
#     obj = get_object_or_404(ClassTeacherAssignment, id=assignment_id)

#     if request.method == 'POST':
#         class_assigned = request.POST.get('class_assigned')
#         subject = request.POST.get('subject')
#         teacher = request.POST.get('teacher')

#         try:
#             with transaction.atomic():   # atomic transaction to ensure data integrity
#                 obj.class_assigned_id = class_assigned
#                 obj.subject_id = subject
#                 obj.teacher_id = teacher
#                 obj.save()
#         except IntegrityError:
#             messages.error(request, 'This assignment already exists(race)!')
#             return redirect('edit_assignment', assignment_id=assignment_id)
        
#         messages.success(request, 'Assignment Updated successfully!')
#         return redirect('assignment_list')



#     classes = Class.objects.all()
#     subjects = Subject.objects.all()
#     teachers = Teacher.objects.all()
#     context = {
#         'available_classes': classes,
#         'available_subjects': subjects,
#         'available_teachers': teachers,
#         'selected_class': obj.class_assigned,
#         'selected_subject': obj.subject,
#         'selected_teacher': obj.teacher,
#         'assignment': obj,
#     }
#     return render(request, 'subject/edit-assignment.html', context)


@login_required(login_url='login')
def delete_assignment(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(ClassTeacherAssignment, id=assignment_id)
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('assignment_list')
    return HttpResponseForbidden('Cannot delete assignment')

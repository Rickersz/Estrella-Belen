from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Department

@login_required(login_url='login')
def add_department(request):
    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        name = request.POST.get('department_name')
        hod = request.POST.get('hod')
        start_date = request.POST.get('start_date')
        no_of_students = request.POST.get('no_of_students')
        
        Department.objects.create(
            department_id=department_id,
            name=name,
            hod=hod,
            start_date=start_date,
            no_of_students=no_of_students
        )
        messages.success(request, 'Department added successfully!')
        return redirect('department_list')
    
    return render(request, 'department/add-department.html')

@login_required(login_url='login')
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'department/department-list.html', {'departments': departments})

@login_required(login_url='login')
def edit_department(request, department_id):
    department = get_object_or_404(Department, department_id=department_id)

    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        name = request.POST.get('department_name')
        hod = request.POST.get('hod')
        start_date = request.POST.get('start_date')
        no_of_students = request.POST.get('no_of_students')
        
        department.department_id = department_id
        department.name = name
        department.hod = hod
        department.start_date = start_date
        department.no_of_students = no_of_students
        department.save()

        messages.success(request, 'Department updated successfully!')
        # create_notification(request.user, f'Department {department.department_id} {department.name} updated.')        
        return redirect('department_list')
    
    return render(request, 'department/edit-department.html', {'department': department})

@login_required(login_url='login')
def delete_department(request, department_id):
    if request.method == 'POST':
        department = get_object_or_404(Department, department_id=department_id)
        department.delete()
        messages.success(request, f'Department {department} deleted successfully!')
        return redirect('department_list')
    return HttpResponseForbidden('Cannot delete department')


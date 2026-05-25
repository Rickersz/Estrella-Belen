
def dashboards(request):
    dashboards = [] 
    user = request.user
    if hasattr(user, 'is_admin') and user.is_admin:
        dashboards.append({'url_name': 'admin_dashboard', 'display_name': 'Admin Dashboard'})        
    if hasattr(user, 'is_teacher') and user.is_teacher:
        dashboards.append({'url_name': 'teacher_dashboard', 'display_name': 'Teacher Dashboard'})
    if hasattr(user, 'is_student') and user.is_student:     # check if user has student attribute and is a student
        dashboards.append({'url_name': 'student_dashboard', 'display_name': 'Student Dashboard'})  

    return {'dashboards': dashboards}
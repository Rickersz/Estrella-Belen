
def dashboards(request):
    dashboards = [] 
    user = request.user
    if hasattr(user, 'is_admin') and user.is_admin:
        dashboards.append({'url_name': 'admin_dashboard', 'display_name': 'Panel administrador'})
    if hasattr(user, 'is_teacher') and user.is_teacher:
        dashboards.append({'url_name': 'teacher_dashboard', 'display_name': 'Panel profesor'})
    if hasattr(user, 'is_representative') and user.is_representative:
        dashboards.append({'url_name': 'representative_dashboard', 'display_name': 'Representante'})
    if hasattr(user, 'is_student') and user.is_student:
        dashboards.append({'url_name': 'student_dashboard', 'display_name': 'Panel estudiante'})

    return {'dashboards': dashboards}

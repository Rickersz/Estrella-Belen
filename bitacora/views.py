from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import AccessLog


def is_admin(user):
    return hasattr(user, 'is_admin') and user.is_admin


@login_required(login_url='iniciar_sesion')
@user_passes_test(is_admin, login_url='iniciar_sesion')
def access_log_list(request):
    logs = AccessLog.objects.all()
    return render(request, 'bitacora/access_log_list.html', {'logs': logs})

from .models import AuditLog


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(request, action, obj=None, description=''):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=str(getattr(obj, 'pk', '')) if obj else '',
        description=description,
        ip_address=client_ip(request),
    )

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse

from estudiante.models import Student
from escuela.models import ClassTeacherAssignment, Notification
from profesor.models import Teacher
from .models import WhatsAppMessageLog


def is_admin(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


def is_teacher(user):
    return user.is_authenticated and getattr(user, 'is_teacher', False)


def is_representative(user):
    return user.is_authenticated and getattr(user, 'is_representative', False)


def can_manage_academic(user):
    return is_admin(user) or is_teacher(user)


def teacher_for_user(user):
    return Teacher.objects.filter(email__iexact=user.email).first()


def teacher_sections(user):
    teacher = teacher_for_user(user)
    if not teacher:
        return []
    return list(ClassTeacherAssignment.objects.filter(teacher=teacher, is_active=True).values_list('class_assigned__section', flat=True).distinct())


def students_for_user(user):
    qs = Student.objects.select_related('parent')
    if is_admin(user):
        return qs
    if is_teacher(user):
        sections = teacher_sections(user)
        return qs.filter(section__in=sections) if sections else qs.none()
    if is_representative(user):
        parent = getattr(user, 'representante', None)
        return qs.filter(parent=parent) if parent else qs.none()
    return qs.none()


def announcement_recipients(audience):
    User = get_user_model()
    qs = User.objects.filter(is_active=True)
    if audience == 'administradores':
        return qs.filter(is_admin=True)
    if audience == 'profesores':
        return qs.filter(is_teacher=True)
    if audience == 'representantes':
        return qs.filter(is_representative=True)
    return qs.filter(is_admin=True) | qs.filter(is_teacher=True) | qs.filter(is_representative=True)


def notify_announcement(announcement):
    users = announcement_recipients(announcement.audience).distinct()
    for user in users:
        Notification.objects.get_or_create(user=user, message=f'Anuncio: {announcement.title}')
        if announcement.send_email and user.email:
            send_mail(
                f'Anuncio institucional: {announcement.title}',
                announcement.body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        if announcement.send_whatsapp:
            phone = getattr(getattr(user, 'representante', None), 'father_mobile', '') or getattr(getattr(user, 'representante', None), 'mother_mobile', '')
            if phone:
                send_whatsapp(phone, f'{announcement.title}\n{announcement.body}')


def send_whatsapp(recipient, message):
    log = WhatsAppMessageLog.objects.create(recipient=recipient, message=message, status='pendiente')
    if not settings.WHATSAPP_API_URL:
        log.status = 'sin_configuracion'
        log.response = 'WHATSAPP_API_URL no configurado.'
        log.save(update_fields=['status', 'response'])
        return log
    try:
        headers = {}
        if settings.WHATSAPP_API_TOKEN:
            headers['Authorization'] = f'Bearer {settings.WHATSAPP_API_TOKEN}'
        response = requests.post(settings.WHATSAPP_API_URL, json={'to': recipient, 'message': message}, headers=headers, timeout=10)
        log.status = 'enviado' if response.ok else 'error'
        log.response = response.text[:1000]
    except Exception as exc:
        log.status = 'error'
        log.response = str(exc)
    log.save(update_fields=['status', 'response'])
    return log


def xlsx_response(filename, headers, rows):
    shared_rows = [headers] + [[str(value) if value is not None else '' for value in row] for row in rows]
    sheet_rows = []
    for r_idx, row in enumerate(shared_rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            col = chr(64 + c_idx)
            safe = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            cells.append(f'<c r="{col}{r_idx}" t="inlineStr"><is><t>{safe}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    sheet_xml = f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    workbook_xml = '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Datos" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', rels)
        archive.writestr('xl/workbook.xml', workbook_xml)
        archive.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        archive.writestr('xl/worksheets/sheet1.xml', sheet_xml)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

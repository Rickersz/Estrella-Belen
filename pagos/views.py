from io import BytesIO

from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from escuela.models import AuditLog, Notification
from estudiante.models import Student
from academico.utils import xlsx_response
from .forms import PaymentConfigForm, PaymentForm, PaymentGenerationForm, RepresentativePaymentForm
from .models import Payment, PaymentConfig
from .utils import can_manage_payments, can_view_payments, create_payment_notifications, is_admin, is_representative, refresh_overdue_payments


def get_representative_parent(user):
    return getattr(user, 'representante', None)


def log_audit(request, action, obj=None, description=''):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=str(getattr(obj, 'pk', '')) if obj else '',
        description=description,
        ip_address=ip_address,
    )


def payment_queryset_for_user(user):
    qs = Payment.objects.select_related('student', 'representative', 'representative__user', 'created_by')
    if is_admin(user):
        return qs
    parent = get_representative_parent(user)
    if parent:
        return qs.filter(representative=parent)
    return qs.none()


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def payment_dashboard(request):
    refresh_overdue_payments()
    create_payment_notifications()
    payments = payment_queryset_for_user(request.user)
    pending = payments.filter(status__in=[Payment.STATUS_PENDING, Payment.STATUS_PARTIAL, Payment.STATUS_OVERDUE])
    context = {
        'total_payments': payments.count(),
        'paid_count': payments.filter(status=Payment.STATUS_PAID).count(),
        'pending_count': pending.count(),
        'overdue_count': payments.filter(status=Payment.STATUS_OVERDUE).count(),
        'total_debt': pending.aggregate(total=Sum('balance'))['total'] or 0,
        'recent_payments': payments[:8],
        'upcoming_payments': pending.order_by('due_date')[:8],
        'configs': PaymentConfig.objects.filter(is_active=True),
    }
    template = 'pagos/dashboard_representante.html' if is_representative(request.user) and not is_admin(request.user) else 'pagos/dashboard.html'
    return render(request, template, context)


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def payment_list(request):
    refresh_overdue_payments()
    payments = payment_queryset_for_user(request.user)
    status = request.GET.get('estado', '')
    query = request.GET.get('q', '').strip()
    if status:
        payments = payments.filter(status=status)
    if query:
        payments = payments.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__student_id__icontains=query) |
            Q(reference__icontains=query)
        )
    paginator = Paginator(payments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'pagos/lista_pagos.html', {
        'payments': page_obj,
        'page_obj': page_obj,
        'status': status,
        'query': query,
        'status_choices': Payment.STATUS_CHOICES,
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def payment_create(request):
    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.created_by = request.user
        payment.save()
        notify_payment(payment)
        log_audit(request, 'crear_pago', payment, f'Registro pago para {payment.student}.')
        messages.success(request, 'Pago registrado correctamente.')
        return redirect('payment_detail', pk=payment.pk)
    return render(request, 'pagos/form_pago.html', {'form': form, 'title': 'Registrar pago'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    form = PaymentForm(request.POST or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        payment = form.save()
        notify_payment(payment)
        log_audit(request, 'editar_pago', payment, f'Actualizo pago para {payment.student}.')
        messages.success(request, 'Pago actualizado correctamente.')
        return redirect('payment_detail', pk=payment.pk)
    return render(request, 'pagos/form_pago.html', {'form': form, 'payment': payment, 'title': 'Editar pago'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def payment_detail(request, pk):
    payment = get_object_or_404(payment_queryset_for_user(request.user), pk=pk)
    return render(request, 'pagos/detalle_pago.html', {'payment': payment})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def representative_pay(request, pk):
    payment = get_object_or_404(payment_queryset_for_user(request.user), pk=pk)
    if not is_representative(request.user) and not is_admin(request.user):
        return HttpResponseForbidden('No autorizado')
    if payment.verification_status == Payment.VERIFICATION_PENDING:
        messages.info(request, 'Este pago ya tiene un reporte pendiente por verificar.')
        return redirect('payment_detail', pk=payment.pk)
    form = RepresentativePaymentForm(request.POST or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated.reported_by = request.user
        updated.reported_at = timezone.now()
        updated.verification_status = Payment.VERIFICATION_PENDING
        updated.save()
        Notification.objects.create(
            user=updated.created_by or request.user,
            message=f'Pago reportado pendiente por verificar: {updated.student.first_name} {updated.student.last_name}.',
        )
        log_audit(request, 'reportar_pago', updated, f'Reporto pago por {updated.reported_amount}.')
        messages.success(request, 'Pago reportado correctamente. Administracion lo verificara antes de marcarlo como pagado.')
        return redirect('payment_detail', pk=updated.pk)
    return render(request, 'pagos/form_pago_representante.html', {'form': form, 'payment': payment})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
@require_POST
def approve_reported_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk, verification_status=Payment.VERIFICATION_PENDING)
    payment.amount_paid = min(payment.amount_due, (payment.amount_paid or 0) + (payment.reported_amount or 0))
    payment.reference = payment.reported_reference or payment.reference
    payment.verified_by = request.user
    payment.verified_at = timezone.now()
    payment.verification_status = Payment.VERIFICATION_APPROVED
    payment.save()
    notify_payment(payment)
    log_audit(request, 'aprobar_pago_reportado', payment, f'Aprobo pago reportado por {payment.reported_amount}.')
    messages.success(request, 'Pago reportado aprobado y aplicado al saldo.')
    return redirect('payment_detail', pk=payment.pk)


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
@require_POST
def reject_reported_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk, verification_status=Payment.VERIFICATION_PENDING)
    payment.verification_status = Payment.VERIFICATION_REJECTED
    payment.verified_by = request.user
    payment.verified_at = timezone.now()
    payment.save(update_fields=['verification_status', 'verified_by', 'verified_at', 'updated_at'])
    notify_payment(payment)
    log_audit(request, 'rechazar_pago_reportado', payment, f'Rechazo pago reportado por {payment.reported_amount}.')
    messages.warning(request, 'Pago reportado rechazado.')
    return redirect('payment_detail', pk=payment.pk)


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def payment_config_list(request):
    configs = PaymentConfig.objects.all()
    return render(request, 'pagos/config_list.html', {'configs': configs})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def payment_config_create(request):
    form = PaymentConfigForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_audit(request, 'crear_configuracion_pago', None, 'Creo una configuracion de pago.')
        messages.success(request, 'Configuracion de pago guardada.')
        return redirect('payment_config_list')
    return render(request, 'pagos/config_form.html', {'form': form})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def generate_recurring_payments(request):
    form = PaymentGenerationForm(request.POST or None, initial={'month': timezone.localdate().month, 'year': timezone.localdate().year})
    created = 0
    skipped = 0
    if request.method == 'POST' and form.is_valid():
        config = form.cleaned_data['config']
        due_date = form.cleaned_data['due_date']
        students = Student.objects.select_related('parent').filter(is_archived=False)
        for student in students:
            _, was_created = Payment.objects.get_or_create(
                student=student,
                concept=config.name,
                academic_year=config.academic_year,
                due_date=due_date,
                defaults={
                    'representative': student.parent,
                    'amount_due': config.amount,
                    'created_by': request.user,
                },
            )
            if was_created:
                created += 1
            else:
                skipped += 1
        log_audit(request, 'generar_pagos_recurrentes', config, f'Genero {created} pagos y omitio {skipped} duplicados.')
        messages.success(request, f'Pagos generados: {created}. Existentes omitidos: {skipped}.')
        return redirect('payment_list')
    return render(request, 'pagos/generar_pagos.html', {'form': form, 'created': created, 'skipped': skipped})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def solvent_students(request):
    students = Student.objects.select_related('parent').filter(is_archived=False).annotate(
        open_payments=Count('payments', filter=Q(payments__balance__gt=0))
    ).filter(open_payments=0)
    return render(request, 'pagos/estudiantes_estado.html', {'students': students, 'title': 'Estudiantes solventes'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_payments, login_url='iniciar_sesion')
def delinquent_students(request):
    students = Student.objects.select_related('parent').filter(is_archived=False, payments__status=Payment.STATUS_OVERDUE).distinct()
    return render(request, 'pagos/estudiantes_estado.html', {'students': students, 'title': 'Estudiantes morosos'})


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def payment_receipt_pdf(request, pk):
    payment = get_object_or_404(payment_queryset_for_user(request.user), pk=pk)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(inch, y, 'Comprobante de Pago')
    y -= 0.35 * inch
    pdf.setFont('Helvetica', 10)
    rows = [
        ('Estudiante', f'{payment.student.first_name} {payment.student.last_name}'),
        ('Representante', payment.representative_name),
        ('Concepto', payment.concept),
        ('Ano escolar', payment.academic_year),
        ('Fecha limite', payment.due_date.strftime('%d/%m/%Y')),
        ('Fecha de pago', payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '-'),
        ('Estado', payment.get_status_display()),
        ('Monto a pagar', f'{payment.amount_due:.2f}'),
        ('Monto pagado', f'{payment.amount_paid:.2f}'),
        ('Saldo pendiente', f'{payment.balance:.2f}'),
        ('Referencia', payment.reference or '-'),
    ]
    for label, value in rows:
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(inch, y, f'{label}:')
        pdf.setFont('Helvetica', 10)
        pdf.drawString(2.4 * inch, y, str(value))
        y -= 0.25 * inch
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(inch, 0.75 * inch, f'Emitido el {timezone.localtime().strftime("%d/%m/%Y %H:%M")}')
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_pago_{payment.pk}.pdf"'
    return response


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_view_payments, login_url='iniciar_sesion')
def export_payments_excel(request):
    payments = payment_queryset_for_user(request.user).select_related('student', 'representative')
    rows = [
        [
            payment.student.student_id,
            f'{payment.student.first_name} {payment.student.last_name}',
            payment.representative_name,
            payment.concept,
            payment.academic_year,
            payment.due_date,
            payment.payment_date or '',
            payment.get_status_display(),
            payment.amount_due,
            payment.amount_paid,
            payment.balance,
            payment.get_verification_status_display(),
            payment.reference,
        ]
        for payment in payments
    ]
    headers = [
        'Cedula escolar', 'Estudiante', 'Representante', 'Concepto', 'Ano escolar',
        'Fecha limite', 'Fecha de pago', 'Estado', 'Monto', 'Pagado', 'Saldo',
        'Revision', 'Referencia',
    ]
    return xlsx_response('pagos.xlsx', headers, rows)


def notify_payment(payment):
    parent = payment.representative
    if parent and parent.user:
        Notification.objects.create(
            user=parent.user,
            message=f'Pago {payment.get_status_display()}: {payment.student.first_name} {payment.student.last_name}. Saldo {payment.balance}.'
        )

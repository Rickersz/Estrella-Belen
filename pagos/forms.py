import calendar

from django import forms
from django.utils import timezone

from estudiante.models import Student
from .models import Payment, PaymentConfig


class PaymentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.select_related('parent').order_by('last_name', 'first_name'),
        label='Estudiante',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Payment
        fields = [
            'student', 'concept', 'academic_year', 'due_date', 'payment_date',
            'amount_due', 'amount_paid', 'reference', 'notes',
        ]
        widgets = {
            'concept': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        amount_due = cleaned.get('amount_due') or 0
        amount_paid = cleaned.get('amount_paid') or 0
        payment_date = cleaned.get('payment_date')
        if amount_paid > 0 and not payment_date:
            cleaned['payment_date'] = timezone.localdate()
        if amount_paid > amount_due:
            self.add_error('amount_paid', 'El monto pagado no puede ser mayor al monto a pagar.')
        return cleaned


class RepresentativePaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['reported_amount', 'payment_date', 'reported_reference', 'notes']
        labels = {
            'reported_amount': 'Monto reportado',
            'reported_reference': 'Referencia',
        }
        widgets = {
            'reported_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reported_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_reported_amount(self):
        amount = self.cleaned_data['reported_amount']
        if amount <= 0:
            raise forms.ValidationError('El monto reportado debe ser mayor a cero.')
        if self.instance and self.instance.balance and amount > self.instance.balance:
            raise forms.ValidationError('El monto reportado no puede ser mayor al saldo pendiente.')
        return amount


class PaymentConfigForm(forms.ModelForm):
    class Meta:
        model = PaymentConfig
        fields = ['name', 'academic_year', 'amount', 'due_day', 'allowed_days', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'allowed_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_due_day(self):
        due_day = self.cleaned_data['due_day']
        if due_day < 1 or due_day > 31:
            raise forms.ValidationError('El dia de vencimiento debe estar entre 1 y 31.')
        return due_day


class PaymentGenerationForm(forms.Form):
    config = forms.ModelChoiceField(
        queryset=PaymentConfig.objects.filter(is_active=True),
        label='Concepto configurado',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    month = forms.IntegerField(
        label='Mes',
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'})
    )
    year = forms.IntegerField(
        label='Ano',
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'})
    )

    def clean(self):
        cleaned = super().clean()
        config = cleaned.get('config')
        month = cleaned.get('month')
        year = cleaned.get('year')
        if config and month and year:
            last_day = calendar.monthrange(year, month)[1]
            cleaned['due_date'] = timezone.datetime(year, month, min(config.due_day, last_day)).date()
        return cleaned

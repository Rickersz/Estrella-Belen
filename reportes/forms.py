from django import forms
from .models import Constancia
from estudiante.models import Student


class StudentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        grado = obj.grado or obj.student_class or 'Sin grado'
        return f'{obj.first_name} {obj.last_name} - {obj.student_id} - {grado}'


class ConstanciaForm(forms.ModelForm):
    student = StudentChoiceField(
        queryset=Student.objects.order_by('first_name', 'last_name'),
        label='Estudiante',
        widget=forms.Select(attrs={'class': 'form-control', 'data-searchable-students': 'true'})
    )

    class Meta:
        model = Constancia
        fields = [
            'report_type', 'student', 'academic_year', 'representative_name',
            'representative_id', 'amount_paid', 'solvent_until',
            'behavior_rating', 'reason', 'notes',
        ]
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_report_type'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-2026'}),
            'representative_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional, para solvencia'}),
            'representative_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cedula del representante'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'solvent_until': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Agosto del ano escolar 2024-2025'}),
            'behavior_rating': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')

        if report_type == Constancia.TIPO_SOLVENCIA and not cleaned_data.get('solvent_until'):
            self.add_error('solvent_until', 'Indica hasta que mes o periodo esta solvente.')

        if report_type == Constancia.TIPO_COMPORTAMIENTO and not cleaned_data.get('behavior_rating'):
            self.add_error('behavior_rating', 'Selecciona el comportamiento.')

        return cleaned_data

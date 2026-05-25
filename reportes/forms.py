from django import forms
from .models import Constancia
from estudiante.models import Student


class ConstanciaForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.order_by('first_name', 'last_name'),
        label='Estudiante'
    )

    class Meta:
        model = Constancia
        fields = ['title', 'student', 'reason', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

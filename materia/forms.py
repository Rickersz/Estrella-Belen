from django import forms
from escuela.models import ClassTeacherAssignment, Class
from .models import Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'class_level']

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        queryset = Subject.objects.filter(code__iexact=code)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ya existe una materia con este cÃ³digo.')
        return code

    def clean_name(self):
        return self.cleaned_data['name'].strip().title()

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = ClassTeacherAssignment
        fields = ['class_assigned', 'subject', 'teacher']
        
        widgets = {
            'class_assigned': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_assigned'].empty_label = "Selecciona una clase"
        self.fields['subject'].empty_label = "Selecciona una materia"
        self.fields['teacher'].empty_label = "Selecciona un profesor"

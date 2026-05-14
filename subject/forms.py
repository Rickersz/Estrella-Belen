from django import forms
from school.models import ClassTeacherAssignment, Class

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
        self.fields['class_assigned'].empty_label = "Select Class"
        self.fields['subject'].empty_label = "Select Subject"
        self.fields['teacher'].empty_label = "Select Teacher"
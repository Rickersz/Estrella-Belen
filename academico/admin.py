from django.contrib import admin

from .models import AcademicGrade, Announcement, ClassSchedule, CommunicationMessage, DisciplineObservation, SchoolEvent, WhatsAppMessageLog


admin.site.register(AcademicGrade)
admin.site.register(ClassSchedule)
admin.site.register(SchoolEvent)
admin.site.register(DisciplineObservation)
admin.site.register(Announcement)
admin.site.register(CommunicationMessage)
admin.site.register(WhatsAppMessageLog)

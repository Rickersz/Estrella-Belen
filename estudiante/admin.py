from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Parent, Enrollment


# =========================
# PARENT ADMIN
# =========================
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    fieldsets = (
        ("👨 Padre", {
            "fields": (
                "father_name",
                "father_mobile",
                "father_email",
                "cedula_padre",
                "fechan_padre",
                "trabaja_padre",
                "lugar_trabajo_padre",
            )
        }),
        ("👩 Madre", {
            "fields": (
                "mother_name",
                "mother_mobile",
                "mother_email",
                "fechan_madre",
                "trabaja_madre",
                "lugar_trabajo_madre",
            )
        }),
    )

    search_fields = ('father_name', 'mother_name')
    list_display = ('father_name', 'mother_name', 'father_mobile', 'mother_mobile')


# =========================
# STUDENT ADMIN (PRO)
# =========================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    # 👇 IMAGEN PREVIEW
    def image_tag(self, obj):
        if obj.student_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                obj.student_image.url
            )
        return "No image"

    image_tag.short_description = "Foto"

    list_display = (
        'image_tag',
        'student_id',
        'first_name',
        'last_name',
        'etapa',
        'grado',
        'section',
        'gender',
        'tiene_cedula',
    )

    search_fields = (
        'student_id',
        'first_name',
        'last_name',
        'cedula',
    )

    list_filter = (
        'etapa',
        'grado',
        'section',
        'gender',
        'discapacidad',
        'repitiente',
        'vive_con_padres',
        'huerfano',
    )

    fieldsets = (
        ("🧑 Identidad", {
            "fields": (
                "student_id",
                "first_name",
                "last_name",
                "tiene_cedula",
                "cedula",
                "nacionalidad",
                "estado_natal",
                "edad",
                "etnia",
                "pais_extranjero",
                "direccion_completa",
                "student_image",
            )
        }),

        ("🎓 Académico", {
            "fields": (
                "etapa",
                "grado",
                "section",
                "admission_number",
                "joining_date",
                "date_of_birth",
            )
        }),

        ("👕 Tallas y Transporte", {
            "fields": (
                "pantalon",
                "camisa",
                "calzado",
                "peso",
                "estatura",
                "transporte",
            )
        }),

        ("🏠 Familia", {
            "fields": (
                "vive_con_padres",
                "huerfano",
            )
        }),

        ("🏥 Salud", {
            "fields": (
                "discapacidad",
                "condicion",
                "area_condicion",
                "tipo_discapacidad",
                "carnet_discapacidad",
                "informe_medico",
                "recibe_tratamiento",
                "cual_tratamiento",
            )
        }),

        ("📚 Escolaridad", {
            "fields": (
                "plantel_anterior",
                "repitiente",
                "aula_integrada",
                "cargado_sge",
                "observaciones",
            )
        }),
    )


# =========================
# ENROLLMENT ADMIN
# =========================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'academic_year',
        'etapa',
        'grado',
        'section',
        'status',
        'date_enrolled',
    )

    list_filter = (
        'academic_year',
        'etapa',
        'grado',
        'status',
    )

    search_fields = (
        'student__first_name',
        'student__last_name',
        'student__student_id',
    )
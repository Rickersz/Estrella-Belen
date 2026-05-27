from django.urls import path

from . import views


urlpatterns = [
    path('', views.payment_dashboard, name='payment_dashboard'),
    path('lista/', views.payment_list, name='payment_list'),
    path('registrar/', views.payment_create, name='payment_create'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/editar/', views.payment_edit, name='payment_edit'),
    path('<int:pk>/pagar/', views.representative_pay, name='representative_pay'),
    path('<int:pk>/comprobante/', views.payment_receipt_pdf, name='payment_receipt_pdf'),
    path('configuracion/', views.payment_config_list, name='payment_config_list'),
    path('configuracion/nueva/', views.payment_config_create, name='payment_config_create'),
    path('solventes/', views.solvent_students, name='solvent_students'),
    path('morosos/', views.delinquent_students, name='delinquent_students'),
]

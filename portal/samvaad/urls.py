from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from operations import views as v
urlpatterns=[
 path('healthz',v.health,name='health'),path('setup/',v.bootstrap,name='setup'),
 path('login/',v.SecureLogin.as_view(),name='login'),path('logout/',auth_views.LogoutView.as_view(),name='logout'),
 path('password/change/',auth_views.PasswordChangeView.as_view(template_name='operations/form.html',success_url='/'),name='password_change'),
 path('admin/',admin.site.urls),path('',v.dashboard,name='dashboard'),path('edition/',v.select_edition,name='select_edition'),
 path('participants/',v.participants,name='participants'),path('participants/new/',v.nomination,name='nominate'),
 path('participants/import/',v.import_people,name='import_people'),path('participants/template.csv',v.import_template,name='import_template'),path('participants/import-results.csv',v.import_errors,name='import_errors'),
 path('participants/<uuid:pk>/',v.participant_detail,name='participant_detail'),path('participants/<uuid:pk>/edit/',v.nomination,name='edit_nomination'),
 path('participants/<uuid:pk>/journey/<str:action>/',v.journey_action,name='journey_action'),path('participants/<uuid:pk>/service/<str:kind>/',v.service_form,name='service_form'),
 path('participants/<uuid:pk>/bank/',v.bank_view,name='bank_view'),path('participants/<uuid:pk>/bank/verify/',v.verify_bank,name='verify_bank'),
 path('stays/<uuid:pk>/<str:action>/',v.accommodation_action,name='stay_action'),
 path('finance/',v.finance_list,name='finance'),path('finance/<uuid:pk>/<str:action>/',v.finance_action,name='finance_action'),
 path('badges/<uuid:pk>/',v.badge_print,name='badge_print'),path('badges/<uuid:pk>/qr.svg',v.badge_qr,name='badge_qr'),
 path('reports/',v.reports,name='reports'),path('my-visit/',v.my_visit,name='my_visit'),
 path('operations/<str:resource>/',v.module,name='module'),path('operations/<str:resource>/<str:model_name>/new/',v.config_edit,name='config_create'),
 path('operations/<str:resource>/<str:model_name>/<uuid:pk>/edit/',v.config_edit,name='config_edit'),
]

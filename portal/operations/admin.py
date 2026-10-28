from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import *
admin.site.site_header='Samvaad 360 administration'
admin.site.site_title='Samvaad 360'
admin.site.index_title='Event, staff and access configuration'
# The administrator console is a privileged boundary, not an operational staff UI.
admin.site.has_permission=lambda request: bool(request.user.is_active and request.user.is_superuser)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display=('user','edition','role','stream','active');list_filter=('edition','role','active');search_fields=('user__username',)

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display=('name','state','user');search_fields=('name','phone');exclude=('community',)

for model in [Event,Edition,Unit,EditionUnit,RolePermission]:admin.site.register(model)

class ReadOnlyAudit(admin.ModelAdmin):
    def has_add_permission(self,*a,**kw):return False
    def has_change_permission(self,*a,**kw):return False
    def has_delete_permission(self,*a,**kw):return False
    def get_readonly_fields(self,request,obj=None):return [f.name for f in self.model._meta.fields]

for model in [Audit,Receipt,Badge,Stay,Passenger,KitIssue,MealIssue,Attendance,Claim]:admin.site.register(model,ReadOnlyAudit)
# Bank ciphertext and assistance records deliberately have no generic admin editor.

for model in [ParticipantCategory,TribeReference]:admin.site.register(model)
admin.site.register(Notification,ReadOnlyAudit)

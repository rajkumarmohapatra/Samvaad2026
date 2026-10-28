from django.db import migrations

def backfill(apps,schema_editor):
    Audit=apps.get_model('operations','Audit');Notification=apps.get_model('operations','Notification')
    for row in Audit.objects.all().iterator(chunk_size=500):
        n,created=Notification.objects.get_or_create(id=row.id,defaults={'edition_id':row.edition_id,'actor_id':row.actor_id,'participation_id':row.participation_id,'action':row.action,'severity':'info','message':row.action.replace('.',' ').replace('_',' ').capitalize()[:240],'page_name':'Historical audit','page_path':'(page not recorded previously)'})
        if created:Notification.objects.filter(pk=n.pk).update(created_at=row.created_at)

class Migration(migrations.Migration):
    dependencies=[('operations','0003_participantcategory_tribereference_and_more')]
    operations=[migrations.RunPython(backfill,migrations.RunPython.noop)]

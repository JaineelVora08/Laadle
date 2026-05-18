from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('direct_messaging_service', '0002_query_nullable_domain_name'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='directmessage',
            index=models.Index(fields=['chat_request', '-sent_at'], name='direct_mess_chat_r_9f07fb_idx'),
        ),
    ]

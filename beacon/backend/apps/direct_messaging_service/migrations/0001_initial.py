import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('query_orchestrator', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('intro_message', models.TextField(blank=True, default='')),
                ('status', models.CharField(
                    choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')],
                    default='PENDING',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dm_requests_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('senior', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dm_requests_received',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('query', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='chat_requests',
                    to='query_orchestrator.query',
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'app_label': 'direct_messaging_service',
            },
        ),
        migrations.AlterUniqueTogether(
            name='chatrequest',
            unique_together={('student', 'senior', 'query')},
        ),
        migrations.CreateModel(
            name='DirectMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('chat_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='direct_messaging_service.chatrequest',
                )),
                ('sender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dm_messages_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['sent_at'],
                'app_label': 'direct_messaging_service',
            },
        ),
    ]

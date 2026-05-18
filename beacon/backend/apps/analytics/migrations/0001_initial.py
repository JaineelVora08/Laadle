import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(max_length=100)),
                ('actor_id', models.UUIDField(blank=True, null=True)),
                ('query_id', models.UUIDField(blank=True, null=True)),
                ('payload', models.JSONField(default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['event_type', '-timestamp'], name='analytics_e_event_t_52fb8d_idx'),
                    models.Index(fields=['query_id', '-timestamp'], name='analytics_e_query_i_baf7fe_idx'),
                ],
            },
        ),
    ]

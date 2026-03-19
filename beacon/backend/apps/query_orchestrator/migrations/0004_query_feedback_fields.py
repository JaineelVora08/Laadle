from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query_orchestrator', '0003_multi_domain_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='student_rating',
            field=models.IntegerField(blank=True, help_text='Student rating 1-5', null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='follow_through_success',
            field=models.BooleanField(blank=True, help_text='Did the advice help?', null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='follow_through_proof',
            field=models.URLField(blank=True, default='', help_text='Optional proof URL'),
        ),
    ]

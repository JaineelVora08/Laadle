from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query_orchestrator', '0006_majority_finalization'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='query',
            index=models.Index(fields=['student', '-timestamp'], name='query_orche_student_6cfcf7_idx'),
        ),
        migrations.AddIndex(
            model_name='query',
            index=models.Index(fields=['status', '-timestamp'], name='query_orche_status_58e6f6_idx'),
        ),
        migrations.AddIndex(
            model_name='query',
            index=models.Index(fields=['status', 'is_cluster_lead', 'response_deadline'], name='query_orche_status_5d3e2e_idx'),
        ),
        migrations.AddIndex(
            model_name='seniorqueryassignment',
            index=models.Index(fields=['senior', 'status'], name='query_orche_senior_2d3a0d_idx'),
        ),
        migrations.AddIndex(
            model_name='seniorqueryassignment',
            index=models.Index(fields=['query', 'status'], name='query_orche_query_282095_idx'),
        ),
    ]

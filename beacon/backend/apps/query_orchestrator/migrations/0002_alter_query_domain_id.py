from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query_orchestrator', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='domain_id',
            field=models.CharField(max_length=64),
        ),
    ]

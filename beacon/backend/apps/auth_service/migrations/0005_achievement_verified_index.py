from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0004_profile_completed'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='achievement',
            index=models.Index(fields=['user', 'verified'], name='auth_servic_user_id_2c94a2_idx'),
        ),
    ]

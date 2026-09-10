from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_alter_user_managers_user_profile_picture')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='monthly_income',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Optional monthly income used for budget recommendations.', max_digits=14),
        ),
    ]
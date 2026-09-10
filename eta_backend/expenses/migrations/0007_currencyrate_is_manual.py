from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0006_expenseentry_amount_base_eur_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='currencyrate',
            name='is_manual',
            field=models.BooleanField(default=False),
        ),
    ]
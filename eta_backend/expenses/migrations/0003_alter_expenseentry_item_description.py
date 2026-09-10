from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0002_expenseentry_item_description_optional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseentry',
            name='item_description',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]

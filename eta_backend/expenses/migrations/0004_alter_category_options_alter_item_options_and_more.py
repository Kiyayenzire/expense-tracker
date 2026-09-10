from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0003_alter_expenseentry_item_description'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ['description']},
        ),
        migrations.AlterModelOptions(
            name='subcategory',
            options={'ordering': ['name']},
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenseentry',
            name='item_description',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='expenseentry',
            name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='expenses', to='expenses.item'),
        ),
    ]
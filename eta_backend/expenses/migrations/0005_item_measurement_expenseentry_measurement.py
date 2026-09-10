from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('expenses', '0004_alter_category_options_alter_item_options_and_more')]

    operations = [
        migrations.AddField(
            model_name='item',
            name='measurement',
            field=models.CharField(choices=[('pc', 'Piece (pc)'), ('tn', 'Tin (tn)'), ('bt', 'Bottle (bt)'), ('kg', 'Kilogram (kg)'), ('ltr', 'Litre (ltr)'), ('un', 'Unit (un)')], default='pc', max_length=3),
        ),
        migrations.AddField(
            model_name='expenseentry',
            name='measurement',
            field=models.CharField(choices=[('pc', 'Piece (pc)'), ('tn', 'Tin (tn)'), ('bt', 'Bottle (bt)'), ('kg', 'Kilogram (kg)'), ('ltr', 'Litre (ltr)'), ('un', 'Unit (un)')], default='pc', max_length=3),
        ),
    ]
# Generated by Django 2.1 on 2019-01-18 03:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_auto_20190115_1636'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ordergoods',
            old_name='oder',
            new_name='order',
        ),
    ]

# Generated by Django 4.2.21 on 2025-06-17 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0020_alter_auditoriaacciones_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transferenciahistorial',
            name='stock_previo',
            field=models.IntegerField(blank=True, help_text='Stock en la tienda antes de esta transferencia', null=True),
        ),
    ]

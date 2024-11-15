# Generated by Django 5.0.6 on 2024-11-07 04:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_alter_productosvendido_nombre'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producto',
            name='nombre',
        ),
        migrations.AlterField(
            model_name='productosvendido',
            name='nombre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nombre', to='inventario.producto'),
        ),
    ]
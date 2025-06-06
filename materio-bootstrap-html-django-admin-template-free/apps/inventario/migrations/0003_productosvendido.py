# Generated by Django 5.0.6 on 2024-11-07 03:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_tienda'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductosVendido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('cantidad', models.IntegerField(default=0)),
                ('fecha_venta', models.DateTimeField()),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.tienda')),
            ],
        ),
    ]

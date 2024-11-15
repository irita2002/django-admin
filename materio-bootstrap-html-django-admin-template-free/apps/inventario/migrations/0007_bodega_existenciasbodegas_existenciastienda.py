# Generated by Django 5.0.6 on 2024-11-15 02:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0006_producto_nombre_alter_productosvendido_nombre'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bodega',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('cp', models.CharField(max_length=100)),
                ('latitud', models.CharField(max_length=100)),
                ('longitud', models.CharField(max_length=100)),
                ('orden', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ExistenciasBodegas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField(default=0)),
                ('bodega', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.bodega')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.producto')),
            ],
        ),
        migrations.CreateModel(
            name='ExistenciasTienda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField(default=0)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.producto')),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.tienda')),
            ],
        ),
    ]
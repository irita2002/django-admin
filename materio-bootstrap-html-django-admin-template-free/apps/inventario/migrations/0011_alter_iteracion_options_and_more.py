# Generated by Django 5.0.6 on 2025-02-13 08:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0010_transferenciahistorial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='iteracion',
            options={'ordering': ['numero_iteracion'], 'verbose_name': 'Iteración', 'verbose_name_plural': 'Iteraciones'},
        ),
        migrations.AlterUniqueTogether(
            name='iteracion',
            unique_together={('numero_iteracion', 'producto')},
        ),
        migrations.RemoveField(
            model_name='iteracion',
            name='bodega',
        ),
        migrations.RemoveField(
            model_name='iteracion',
            name='orden_entrega',
        ),
    ]

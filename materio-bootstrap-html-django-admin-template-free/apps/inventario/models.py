from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100,default ="")
    cantidad = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre

class Tienda(models.Model):
    nombre = models.CharField(max_length=100)
    latitud = models.CharField(max_length=100)
    longitud = models.CharField(max_length=100)
    TIPO_CHOICES = [('CIMEX', 'CIMEX'), ('TRD', 'TRD')]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES,default="TRD")

    def __str__(self):
        return self.nombre

class ProductosVendido(models.Model):
    nombre = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField()

    def __str__(self):
        return f"{self.nombre}"

class ExistenciasTienda(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)

class Circunscripcion(models.Model):
    """
    Representa la circunscripción (área) donde se ubica una bodega.
    Contiene información sobre núcleos de población vulnerable.
    """
    nombre = models.CharField("Nombre", max_length=100)

    # Núcleos de población vulnerable
    ancianos = models.PositiveIntegerField(
        "Ancianos", default=0,
        help_text="Número de personas de la tercera edad"
    )
    ninos = models.PositiveIntegerField(
        "Niños", default=0,
        help_text="Número de niños"
    )
    embarazadas = models.PositiveIntegerField(
        "Embarazadas", default=0,
        help_text="Número de mujeres embarazadas"
    )

    class Meta:
        verbose_name = "Circunscripción"
        verbose_name_plural = "Circunscripciones"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} "

    @property
    def total_vulnerables(self):
        return self.ancianos + self.ninos + self.embarazadas


class Bodega(models.Model):
    nombre = models.CharField(max_length=100)
    cp = models.ForeignKey(Circunscripcion, on_delete=models.CASCADE)
    cantidad_nucleos = models.IntegerField(default=0)
    latitud = models.CharField(max_length=100)
    longitud = models.CharField(max_length=100)
    orden = models.IntegerField()

    def __str__(self):
        return self.nombre

class ExistenciasBodegas(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE)

class Iteracion(models.Model):
    numero_iteracion = models.IntegerField(verbose_name="Número de Iteración")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    completada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Iteración"
        verbose_name_plural = "Iteraciones"
        unique_together = [['numero_iteracion', 'producto']]
        ordering = ['numero_iteracion']

    def __str__(self):
        return f"Iteración {self.numero_iteracion} - {self.producto.nombre} - {self.completada}"

class TransferenciaHistorial(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha_transferencia = models.DateTimeField()
    iteracion = models.ForeignKey(Iteracion, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-fecha_transferencia']
        verbose_name = "Historial de Transferencia"
        verbose_name_plural = "Historial de Transferencias"

    def __str__(self):
        return f"{self.cantidad} unidades de {self.producto} a {self.bodega}"
        
from django.db import models


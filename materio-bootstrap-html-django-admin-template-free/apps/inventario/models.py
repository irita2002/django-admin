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



class Bodega(models.Model):
    nombre = models.CharField(max_length=100)
    cp = models.CharField(max_length=100)
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
        
# Create your models here.
#class Comunidad(models.Model):
#    nombre = models.CharField(max_length=100)
#    descripcion = models.TextField()
#    administrador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comunidades_administradas')
#    crowusers = models.ManyToManyField(User, related_name='crowusers')
#    miembros = models.ManyToManyField(User, related_name='comunidades')
#    activada = models.BooleanField(default=False)
#    publica = models.BooleanField(default=False)
#    #donaciones = models.BooleanField(default=False)
#    foto_perfil = models.ImageField(upload_to='comunidades/perfiles/', null=True, blank=True, default='comunidades/perfiles/perfil_default.jpg')
#    banner = models.ImageField(upload_to='comunidades/banners/', null=True, blank=True,default='comunidades/banners/banner_default.jpg')
#    #tags = models.ManyToManyField('Tag')
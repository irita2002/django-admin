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
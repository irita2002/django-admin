from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Crea los grupos Coordinador (todos los permisos) y Revisor (solo lectura)'

    def handle(self, *args, **kwargs):
        # Crear grupos
        coordinador_group, _ = Group.objects.get_or_create(name='Coordinador')
        revisor_group, _ = Group.objects.get_or_create(name='Revisor')

        # Obtener todos los permisos
        all_perms = Permission.objects.all()

        # Asignar todos los permisos al grupo Coordinador
        coordinador_group.permissions.set(all_perms)
        self.stdout.write(self.style.SUCCESS('✅ Grupo "Coordinador" tiene todos los permisos.'))

        # Filtrar permisos que solo sean de tipo 'view_'
        view_perms = Permission.objects.filter(codename__startswith='view_')

        # Asignar solo permisos de lectura al grupo Revisor
        revisor_group.permissions.set(view_perms)
        self.stdout.write(self.style.SUCCESS('✅ Grupo "Revisor" tiene solo permisos de lectura.'))

        self.stdout.write(self.style.SUCCESS('🎉 Grupos creados y permisos asignados correctamente.'))

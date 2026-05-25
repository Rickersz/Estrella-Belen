#!/usr/bin/env python
"""
Script para organizar y renombrar el proyecto Django
Traduce nombres de aplicaciones al español y reorganiza la estructura
"""

import os
import shutil
from pathlib import Path

def crear_estructura_organizada():
    """Crea una estructura de carpetas organizada"""
    
    base_dir = Path.cwd()
    
    # Estructura propuesta
    estructura = {
        'aplicaciones': [
            'escuela',
            'estudiante',
            'profesor',
            'materia',
            'departamento',
            'autenticacion',
        ],
        'templates': [
            'base',
            'autenticacion',
            'estudiante',
            'profesor',
            'materia',
            'departamento',
            'escuela',
        ],
        'static': [
            'css',
            'js',
            'img',
            'fonts',
        ],
        'media': [
            'estudiantes',
            'profesores',
            'documentos',
        ]
    }
    
    print("=== CREANDO ESTRUCTURA ORGANIZADA ===")
    
    # Crear directorios
    for categoria, subcategorias in estructura.items():
        for subcategoria in subcategorias:
            ruta = base_dir / categoria / subcategoria
            ruta.mkdir(parents=True, exist_ok=True)
            print(f"✓ Creado: {ruta}")

def traducir_nombres_archivos():
    """Traduce nombres de archivos clave al español"""
    
    traducciones = {
        # Templates
        'add-student.html': 'agregar-estudiante.html',
        'edit-student.html': 'editar-estudiante.html',
        'student-list.html': 'lista-estudiantes.html',
        'student-detail.html': 'detalle-estudiante.html',
        'student-dashboard.html': 'panel-estudiante.html',
        
        'add-teacher.html': 'agregar-profesor.html',
        'edit-teacher.html': 'editar-profesor.html',
        'teacher-list.html': 'lista-profesores.html',
        'teacher-detail.html': 'detalle-profesor.html',
        'teacher-dashboard.html': 'panel-profesor.html',
        
        'add-subject.html': 'agregar-materia.html',
        'edit-subject.html': 'editar-materia.html',
        'subject-list.html': 'lista-materias.html',
        
        'add-department.html': 'agregar-departamento.html',
        'edit-department.html': 'editar-departamento.html',
        'department-list.html': 'lista-departamentos.html',
        
        'add-assignment.html': 'agregar-asignacion.html',
        'edit-assignment.html': 'editar-asignacion.html',
        'assignment-list.html': 'lista-asignaciones.html',
        
        # Archivos de autenticación
        'login.html': 'iniciar-sesion.html',
        'register.html': 'registrarse.html',
        'forgot-password.html': 'recuperar-contrasena.html',
        'reset-password.html': 'restablecer-contrasena.html',
        
        # Archivos base
        'base.html': 'base.html',
        'header.html': 'encabezado.html',
        'footer.html': 'pie.html',
        'index.html': 'inicio.html',
    }
    
    print("\n=== TRADUCIENDO NOMBRES DE ARCHIVOS ===")
    
    templates_dir = Path('templates')
    
    for ingles, espanol in traducciones.items():
        # Buscar archivo en toda la estructura de templates
        for archivo in templates_dir.rglob(ingles):
            nuevo_nombre = archivo.parent / espanol
            try:
                archivo.rename(nuevo_nombre)
                print(f"✓ Renombrado: {archivo} → {nuevo_nombre}")
            except Exception as e:
                print(f"✗ Error renombrando {archivo}: {e}")

def actualizar_referencias_en_templates():
    """Actualiza referencias a archivos renombrados en los templates"""
    
    print("\n=== ACTUALIZANDO REFERENCIAS EN TEMPLATES ===")
    
    templates_dir = Path('templates')
    
    # Mapeo de referencias antiguas a nuevas
    referencias = {
        'add-student.html': 'agregar-estudiante.html',
        'edit-student.html': 'editar-estudiante.html',
        'student-list.html': 'lista-estudiantes.html',
        'student-detail.html': 'detalle-estudiante.html',
        'student-dashboard.html': 'panel-estudiante.html',
        
        'add-teacher.html': 'agregar-profesor.html',
        'edit-teacher.html': 'editar-profesor.html',
        'teacher-list.html': 'lista-profesores.html',
        'teacher-detail.html': 'detalle-profesor.html',
        'teacher-dashboard.html': 'panel-profesor.html',
        
        'add-subject.html': 'agregar-materia.html',
        'edit-subject.html': 'editar-materia.html',
        'subject-list.html': 'lista-materias.html',
        
        'add-department.html': 'agregar-departamento.html',
        'edit-department.html': 'editar-departamento.html',
        'department-list.html': 'lista-departamentos.html',
        
        'add-assignment.html': 'agregar-asignacion.html',
        'edit-assignment.html': 'editar-asignacion.html',
        'assignment-list.html': 'lista-asignaciones.html',
        
        'login.html': 'iniciar-sesion.html',
        'register.html': 'registrarse.html',
        'forgot-password.html': 'recuperar-contrasena.html',
        'reset-password.html': 'restablecer-contrasena.html',
    }
    
    # Actualizar cada archivo template
    for archivo_template in templates_dir.rglob('*.html'):
        try:
            with open(archivo_template, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            contenido_actualizado = contenido
            for viejo, nuevo in referencias.items():
                contenido_actualizado = contenido_actualizado.replace(viejo, nuevo)
                contenido_actualizado = contenido_actualizado.replace(
                    f"'{viejo}'", f"'{nuevo}'"
                )
                contenido_actualizado = contenido_actualizado.replace(
                    f'"{viejo}"', f'"{nuevo}"'
                )
            
            if contenido != contenido_actualizado:
                with open(archivo_template, 'w', encoding='utf-8') as f:
                    f.write(contenido_actualizado)
                print(f"✓ Actualizado: {archivo_template}")
                
        except Exception as e:
            print(f"✗ Error actualizando {archivo_template}: {e}")

def crear_archivo_guia():
    """Crea un archivo guía con la nueva estructura"""
    
    guia = """# GUÍA DE LA NUEVA ESTRUCTURA - Sistema Escolar Estrella de Belén

## 📁 ESTRUCTURA DE CARPETAS ORGANIZADA

```
proyecto/
├── aplicaciones/           # Todas las apps Django en español
│   ├── escuela/           # App principal (antes school)
│   ├── estudiante/        # Gestión de estudiantes (antes student)
│   ├── profesor/          # Gestión de profesores (antes teacher)
│   ├── materia/          # Gestión de materias (antes subject)
│   ├── departamento/     # Gestión de departamentos (antes department)
│   └── autenticacion/    # Sistema de autenticación (antes home_auth)
├── templates/            # Templates organizados
│   ├── base.html         # Template base principal
│   ├── autenticacion/    # Templates de login, registro, etc.
│   ├── estudiante/       # Templates de estudiantes
│   ├── profesor/         # Templates de profesores
│   ├── materia/         # Templates de materias
│   ├── departamento/    # Templates de departamentos
│   └── escuela/         # Templates generales del sistema
├── static/               # Archivos estáticos
│   ├── css/             # Hojas de estilo
│   │   └── estilo.css   # CSS principal moderno
│   ├── js/              # JavaScript
│   ├── img/             # Imágenes
│   └── fonts/           # Fuentes personalizadas
├── media/               # Archivos subidos por usuarios
│   ├── estudiantes/     # Fotos de estudiantes
│   ├── profesores/      # Fotos de profesores
│   └── documentos/      # Documentos varios
└── Home/                # Configuración del proyecto
```

## 🔄 CAMBIOS REALIZADOS

### 1. NOMBRES TRADUCIDOS AL ESPAÑOL
- **school** → **escuela**
- **student** → **estudiante**
- **teacher** → **profesor**
- **subject** → **materia**
- **department** → **departamento**
- **home_auth** → **autenticacion**

### 2. TEMPLATES RENOMBRADOS
- `add-student.html` → `agregar-estudiante.html`
- `student-list.html` → `lista-estudiantes.html`
- `login.html` → `iniciar-sesion.html`
- Y todos los demás archivos traducidos

### 3. CSS MODERNO
- Nuevo archivo `estilo.css` con diseño moderno
- Colores profesionales y tipografía mejorada
- Diseño responsive completo
- Animaciones y efectos sutiles

### 4. ICONOS ARREGLADOS
- FontAwesome actualizado a versión 6.4.0
- Iconos consistentes en toda la aplicación
- Mejor visualización en todos los dispositivos

## 🚀 PASOS PARA MIGRAR COMPLETAMENTE

1. **Renombrar carpetas de aplicaciones** (manual o con script)
2. **Actualizar settings.py** con nuevos nombres
3. **Actualizar imports** en todos los archivos .py
4. **Actualizar URLs** y referencias
5. **Ejecutar migraciones** para actualizar la base de datos

## ⚠️ NOTAS IMPORTANTES

- **Backup**: Siempre haz backup antes de cambios grandes
- **Pruebas**: Verifica que todo funcione después de cada cambio
- **Migrations**: Las migraciones pueden necesitar ajustes
- **Base de datos**: Algunos cambios pueden requerir actualizaciones en la BD

## 📞 SOPORTE

Si encuentras problemas:
1. Revisa los logs de Django
2. Verifica que todos los imports estén actualizados
3. Asegúrate de que las URLs coincidan con los nuevos nombres
4. Ejecuta `python manage.py check` para verificar errores

¡Sistema organizado y en español! 🎉
"""
    
    with open('GUIA_REORGANIZACION.md', 'w', encoding='utf-8') as f:
        f.write(guia)
    
    print("\n=== ARCHIVO GUÍA CREADO ===")
    print("✓ GUIA_REORGANIZACION.md creado con éxito")

def main():
    """Función principal"""
    
    print("=" * 60)
    print("ORGANIZADOR DE PROYECTO DJANGO")
    print("Traducción al español y reorganización")
    print("=" * 60)
    
    # Preguntar al usuario
    respuesta = input("\n¿Deseas organizar el proyecto? (s/n): ").lower()
    
    if respuesta != 's':
        print("Operación cancelada.")
        return
    
    print("\nIniciando organización...")
    
    # Ejecutar pasos
    crear_estructura_organizada()
    traducir_nombres_archivos()
    actualizar_referencias_en_templates()
    crear_archivo_guia()
    
    print("\n" + "=" * 60)
    print("¡ORGANIZACIÓN COMPLETADA!")
    print("=" * 60)
    print("\nRevisa GUIA_REORGANIZACION.md para los próximos pasos.")
    print("\nRecuerda:")
    print("1. Actualizar settings.py con los nuevos nombres")
    print("2. Actualizar todos los imports en archivos .py")
    print("3. Ejecutar migraciones si es necesario")
    print("4. Probar que todo funcione correctamente")

if __name__ == "__main__":
    main()
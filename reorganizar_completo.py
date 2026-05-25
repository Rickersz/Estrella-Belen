#!/usr/bin/env python
"""
Script completo para reorganizar el proyecto Django
Traduce nombres de aplicaciones al español y reorganiza la estructura
Versión mejorada y más segura
"""

import os
import shutil
import re
from pathlib import Path
import sys

def crear_backup():
    """Crea un backup del proyecto antes de hacer cambios"""
    print("=== CREANDO BACKUP DEL PROYECTO ===")
    
    backup_dir = Path.cwd() / "backup_original"
    backup_dir.mkdir(exist_ok=True)
    
    # Copiar archivos importantes
    archivos_importantes = [
        'db.sqlite3',
        'manage.py',
        'requirements.txt',
        '.gitignore',
    ]
    
    for archivo in archivos_importantes:
        if Path(archivo).exists():
            shutil.copy2(archivo, backup_dir / archivo)
            print(f"✓ Backup: {archivo}")
    
    # Copiar carpetas de aplicaciones
    carpetas_apps = ['school', 'student', 'teacher', 'subject', 'department', 'home_auth']
    for carpeta in carpetas_apps:
        if Path(carpeta).exists():
            shutil.copytree(carpeta, backup_dir / carpeta, dirs_exist_ok=True)
            print(f"✓ Backup: {carpeta}/")
    
    print(f"\n✅ Backup completo guardado en: {backup_dir}")
    return backup_dir

def renombrar_aplicaciones():
    """Renombra las aplicaciones de inglés a español"""
    print("\n=== RENOMBRANDO APLICACIONES ===")
    
    mapeo_renombres = {
        'school': 'escuela',
        'student': 'estudiante',
        'teacher': 'profesor',
        'subject': 'materia',
        'department': 'departamento',
        'home_auth': 'autenticacion',
    }
    
    for nombre_ingles, nombre_espanol in mapeo_renombres.items():
        ruta_original = Path(nombre_ingles)
        ruta_nueva = Path(nombre_espanol)
        
        if ruta_original.exists():
            try:
                # Renombrar carpeta
                ruta_original.rename(ruta_nueva)
                print(f"✓ Renombrado: {nombre_ingles} → {nombre_espanol}")
                
                # Actualizar archivos dentro de la app
                actualizar_archivos_en_app(ruta_nueva, nombre_ingles, nombre_espanol)
                
            except Exception as e:
                print(f"✗ Error renombrando {nombre_ingles}: {e}")
        else:
            print(f"⚠ No encontrado: {nombre_ingles}")

def actualizar_archivos_en_app(ruta_app, nombre_viejo, nombre_nuevo):
    """Actualiza imports y referencias dentro de una aplicación"""
    for archivo in ruta_app.rglob('*.py'):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Actualizar imports de la propia app
            contenido = contenido.replace(f'from {nombre_viejo}.', f'from {nombre_nuevo}.')
            contenido = contenido.replace(f'import {nombre_viejo}.', f'import {nombre_nuevo}.')
            
            # Actualizar referencias en strings
            contenido = contenido.replace(f"'{nombre_viejo}.", f"'{nombre_nuevo}.")
            contenido = contenido.replace(f'"{nombre_viejo}.', f'"{nombre_nuevo}.')
            
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
                
        except Exception as e:
            print(f"  ⚠ Error actualizando {archivo}: {e}")

def actualizar_settings_py():
    """Actualiza el archivo settings.py con los nuevos nombres"""
    print("\n=== ACTUALIZANDO SETTINGS.PY ===")
    
    settings_path = Path('Home') / 'settings.py'
    
    if not settings_path.exists():
        print("✗ No se encontró settings.py")
        return
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Mapeo de nombres antiguos a nuevos
        mapeo_apps = {
            "'school',": "'escuela',",
            "'student',": "'estudiante',", 
            "'teacher',": "'profesor',",
            "'subject',": "'materia',",
            "'department',": "'departamento',",
            "'home_auth',": "'autenticacion',",
        }
        
        # Actualizar INSTALLED_APPS
        for viejo, nuevo in mapeo_apps.items():
            contenido = contenido.replace(viejo, nuevo)
        
        # Actualizar AUTH_USER_MODEL
        contenido = contenido.replace(
            "AUTH_USER_MODEL = 'home_auth.CustomUser'",
            "AUTH_USER_MODEL = 'autenticacion.CustomUser'"
        )
        
        # Actualizar AUTHENTICATION_BACKENDS
        contenido = contenido.replace(
            "'home_auth.backends.EmailBackend',",
            "'autenticacion.backends.EmailBackend',"
        )
        
        # Actualizar context processors
        contenido = contenido.replace(
            "'school.context_processors.dashboards',",
            "'escuela.context_processors.dashboards',"
        )
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print("✓ settings.py actualizado correctamente")
        
    except Exception as e:
        print(f"✗ Error actualizando settings.py: {e}")

def actualizar_urls_py():
    """Actualiza el archivo urls.py principal"""
    print("\n=== ACTUALIZANDO URLS.PY ===")
    
    urls_path = Path('Home') / 'urls.py'
    
    if not urls_path.exists():
        print("✗ No se encontró urls.py")
        return
    
    try:
        with open(urls_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Mapeo de imports
        mapeo_imports = {
            "from school.urls": "from escuela.urls",
            "from student.urls": "from estudiante.urls",
            "from teacher.urls": "from profesor.urls",
            "from subject.urls": "from materia.urls",
            "from department.urls": "from departamento.urls",
            "from home_auth.urls": "from autenticacion.urls",
        }
        
        for viejo, nuevo in mapeo_imports.items():
            contenido = contenido.replace(viejo, nuevo)
        
        # Mapeo de includes
        mapeo_includes = {
            "path('', include('school.urls')),": "path('', include('escuela.urls')),",
            "path('student/', include('student.urls')),": "path('estudiante/', include('estudiante.urls')),",
            "path('teacher/', include('teacher.urls')),": "path('profesor/', include('profesor.urls')),",
            "path('subject/', include('subject.urls')),": "path('materia/', include('materia.urls')),",
            "path('department/', include('department.urls')),": "path('departamento/', include('departamento.urls')),",
            "path('home_auth/', include('home_auth.urls')),": "path('autenticacion/', include('autenticacion.urls')),",
        }
        
        for viejo, nuevo in mapeo_includes.items():
            contenido = contenido.replace(viejo, nuevo)
        
        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print("✓ urls.py actualizado correctamente")
        
    except Exception as e:
        print(f"✗ Error actualizando urls.py: {e}")

def actualizar_templates():
    """Actualiza los templates para usar el nuevo diseño"""
    print("\n=== ACTUALIZANDO TEMPLATES ===")
    
    templates_dir = Path('templates')
    
    # Primero, crear estructura de templates organizada
    estructura_templates = {
        'autenticacion': ['iniciar-sesion.html', 'registrarse.html', 'recuperar-contrasena.html'],
        'estudiante': ['lista-estudiantes.html', 'agregar-estudiante.html', 'editar-estudiante.html'],
        'profesor': ['lista-profesores.html', 'agregar-profesor.html', 'editar-profesor.html'],
        'materia': ['lista-materias.html', 'agregar-materia.html', 'editar-materia.html'],
        'departamento': ['lista-departamentos.html', 'agregar-departamento.html', 'editar-departamento.html'],
        'escuela': ['inicio.html', 'panel-admin.html'],
    }
    
    # Crear directorios
    for categoria in estructura_templates.keys():
        (templates_dir / categoria).mkdir(exist_ok=True)
    
    # Buscar y renombrar templates existentes
    mapeo_templates = {
        'login.html': 'iniciar-sesion.html',
        'register.html': 'registrarse.html',
        'forgot-password.html': 'recuperar-contrasena.html',
        
        'student-list.html': 'lista-estudiantes.html',
        'add-student.html': 'agregar-estudiante.html',
        'edit-student.html': 'editar-estudiante.html',
        
        'teacher-list.html': 'lista-profesores.html',
        'add-teacher.html': 'agregar-profesor.html',
        'edit-teacher.html': 'editar-profesor.html',
        
        'subject-list.html': 'lista-materias.html',
        'add-subject.html': 'agregar-materia.html',
        'edit-subject.html': 'editar-materia.html',
        
        'department-list.html': 'lista-departamentos.html',
        'add-department.html': 'agregar-departamento.html',
        'edit-department.html': 'editar-departamento.html',
        
        'index.html': 'inicio.html',
    }
    
    for archivo_template in templates_dir.rglob('*.html'):
        nombre_archivo = archivo_template.name
        
        if nombre_archivo in mapeo_templates:
            nuevo_nombre = mapeo_templates[nombre_archivo]
            
            # Determinar categoría basada en el mapeo
            categoria = None
            if 'student' in nombre_archivo or 'estudiante' in nuevo_nombre:
                categoria = 'estudiante'
            elif 'teacher' in nombre_archivo or 'profesor' in nuevo_nombre:
                categoria = 'profesor'
            elif 'subject' in nombre_archivo or 'materia' in nuevo_nombre:
                categoria = 'materia'
            elif 'department' in nombre_archivo or 'departamento' in nuevo_nombre:
                categoria = 'departamento'
            elif 'login' in nombre_archivo or 'register' in nombre_archivo or 'password' in nombre_archivo:
                categoria = 'autenticacion'
            elif 'index' in nombre_archivo:
                categoria = 'escuela'
            
            if categoria:
                nueva_ruta = templates_dir / categoria / nuevo_nombre
                try:
                    # Leer y actualizar contenido
                    with open(archivo_template, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    
                    # Actualizar extends para usar base.html
                    contenido = re.sub(
                        r"{% extends ['\"].*?base\.html['\"] %}",
                        "{% extends 'base.html' %}",
                        contenido
                    )
                    
                    # Actualizar URLs en templates
                    for viejo, nuevo in mapeo_templates.items():
                        if viejo != nombre_archivo:  # No reemplazar el nombre actual
                            contenido = contenido.replace(viejo, nuevo)
                    
                    # Escribir archivo actualizado
                    with open(nueva_ruta, 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    
                    print(f"✓ Actualizado: {archivo_template} → {nueva_ruta}")
                    
                    # Eliminar archivo original si es diferente
                    if archivo_template != nueva_ruta:
                        archivo_template.unlink()
                        
                except Exception as e:
                    print(f"✗ Error procesando {archivo_template}: {e}")

def actualizar_imports_en_todo_el_proyecto():
    """Actualiza imports en todos los archivos .py del proyecto"""
    print("\n=== ACTUALIZANDO IMPORTS EN TODO EL PROYECTO ===")
    
    mapeo_imports = {
        'school': 'escuela',
        'student': 'estudiante',
        'teacher': 'profesor',
        'subject': 'materia',
        'department': 'departamento',
        'home_auth': 'autenticacion',
    }
    
    # Buscar en todos los archivos .py
    for archivo_py in Path.cwd().rglob('*.py'):
        try:
            with open(archivo_py, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            contenido_original = contenido
            
            # Actualizar imports
            for viejo, nuevo in mapeo_imports.items():
                # Patrones comunes de imports
                patrones = [
                    f'from {viejo} import',
                    f'from {viejo}.',
                    f'import {viejo}',
                    f'{viejo}.',
                ]
                
                for patron in patrones:
                    if patron in contenido:
                        contenido = contenido.replace(
                            f'from {viejo} import',
                            f'from {nuevo} import'
                        )
                        contenido = contenido.replace(
                            f'from {viejo}.',
                            f'from {nuevo}.'
                        )
                        contenido = contenido.replace(
                            f'import {viejo}',
                            f'import {nuevo}'
                        )
            
            # Actualizar referencias en strings
            for viejo, nuevo in mapeo_imports.items():
                contenido = contenido.replace(f"'{viejo}.", f"'{nuevo}.")
                contenido = contenido.replace(f'"{viejo}.', f'"{nuevo}.')
            
            if contenido != contenido_original:
                with open(archivo_py, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                print(f"✓ Actualizado: {archivo_py}")
                
        except Exception as e:
            print(f"✗ Error actualizando {archivo_py}: {e}")

def mejorar_css():
    """Mejora el CSS existente con mejoras adicionales"""
    print("\n=== MEJORANDO CSS ===")
    
    css_path = Path('static') / 'assets' / 'css' / 'estilo.css'
    
    if not css_path.exists():
        print("✗ No se encontró el archivo CSS")
        return
    
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Agregar mejoras al CSS
        mejoras_css = """

/* ========== MEJORAS ADICIONALES ========== */

/* Efectos hover más suaves */
.tarjeta, .btn, .menu-link {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Mejores sombras para profundidad */
.tarjeta {
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}

.tarjeta:hover {
    box-shadow: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
}

/* Gradientes modernos */
.btn-primario {
    background: linear-gradient(135deg, var(--color-secundario) 0%, #2980b9 100%);
}

.btn-exito {
    background: linear-gradient(135deg, var(--color-exito) 0%, #219653 100%);
}

/* Mejores bordes redondeados */
.control-formulario, .btn {
    border-radius: 12px;
}

/* Animaciones para iconos */
.menu-icono {
    transition: transform 0.3s ease;
}

.menu-link:hover .menu-icono {
    transform: scale(1.1);
}

/* Mejores estados de focus */
.control-formulario:focus {
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.25);
    border-color: var(--color-secundario);
}

/* Estilos para modales */
.modal-contenido {
    border-radius: 20px;
    overflow: hidden;
}

.modal-encabezado {
    background: linear-gradient(135deg, var(--color-primario) 0%, #1a252f 100%);
    color: white;
    padding: 1.5rem;
}

/* Mejores alertas */
.alerta {
    border-radius: 12px;
    padding: 1.25rem;
    border-left-width: 6px;
}

/* Estilos para tablas con zebra */
.tabla tbody tr:nth-child(even) {
    background-color: rgba(0, 0, 0, 0.02);
}

/* Mejores badges */
.badge {
    border-radius: 20px;
    padding: 0.35em 0.8em;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Estilos para cards de estadísticas */
.tarjeta-estadistica {
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.tarjeta-estadistica .estadistica-valor {
    font-size: 2.8rem;
    font-weight: 800;
}

/* Efectos de glassmorphism para sidebar */
.barra-lateral {
    backdrop-filter: blur(10px);
    background: rgba(44, 62, 80, 0.95);
}

/* Mejores tooltips */
[tooltip] {
    position: relative;
}

[tooltip]:hover::after {
    content: attr(tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: var(--color-primario);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    white-space: nowrap;
    z-index: 1000;
}

/* Estilos para switches modernos */
.switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
    border-radius: 34px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
}

input:checked + .slider {
    background-color: var(--color-secundario);
}

input:checked + .slider:before {
    transform: translateX(26px);
}

/* ========== FIN DE MEJORAS ========== */
"""
        
        # Agregar las mejoras al final del archivo
        contenido += mejoras_css
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print("✓ CSS mejorado con efectos modernos y animaciones")
        
    except Exception as e:
        print(f"✗ Error mejorando CSS: {e}")

def crear_archivo_guia_final():
    """Crea un archivo guía final con las instrucciones"""
    print("\n=== CREANDO GUÍA FINAL ===")
    
    guia = """# GUÍA DE REORGANIZACIÓN COMPLETADA

## ✅ **CAMBIOS REALIZADOS:**

### 1. **APLICACIONES RENOMBRADAS AL ESPAÑOL**
- `school` → `escuela`
- `student` → `estudiante`
- `teacher` → `profesor`
- `subject` → `materia`
- `department` → `departamento`
- `home_auth` → `autenticacion`

### 2. **CONFIGURACIÓN ACTUALIZADA**
- `settings.py` actualizado con nuevos nombres
- `urls.py` principal actualizado
- Todos los imports en archivos `.py` actualizados

### 3. **TEMPLATES ORGANIZADOS**
- Nuevo template base `base.html` con diseño moderno
- Templates renombrados al español
- Estructura organizada por categorías
- Iconos de FontAwesome funcionando correctamente

### 4. **CSS MEJORADO**
- Archivo `estilo.css` con diseño moderno
- Efectos hover y animaciones suaves
- Diseño responsive completo
- Colores profesionales y tipografía mejorada

### 5. **BACKUP CREADO**
- Carpeta `backup_original` con copia del proyecto original

## 📁 **NUEVA ESTRUCTURA:**

```
proyecto/
├── aplicaciones/ (renombradas)
│   ├── escuela/           # App principal
│   ├── estudiante/        # Gestión de estudiantes
│   ├── profesor/          # Gestión de profesores
│   ├── materia/          # Gestión de materias
│   ├── departamento/     # Gestión de departamentos
│   └── autenticacion/    # Sistema de autenticación
├── templates/            # Templates organizados
│   ├── base.html         # Template base principal
│   ├── autenticacion/    # Login, registro, etc.
│   ├── estudiante/       # Templates de estudiantes
│   ├── profesor/         # Templates de profesores
│   ├── materia/         # Templates de materias
│   ├── departamento/    # Templates de departamentos
│   └── escuela/         # Templates generales
├── static/               # Archivos estáticos
│   ├── assets/
│   │   └── css/
│   │       └── estilo.css  # CSS moderno
└── Home/                # Configuración
```

## 🚀 **PRÓXIMOS PASOS:**

### 1. **EJECUTAR MIGRACIONES**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. **PROBAR FUNCIONALIDAD**
```bash
python manage.py runserver
```

### 3. **VERIFICAR QUE TODO FUNCIONE**
- Login/registro
- CRUD de estudiantes
- CRUD de profesores
- Navegación completa
- Iconos visibles

### 4. **SI HAY PROBLEMAS:**
1. Revisar logs de Django
2. Verificar que todos los imports estén correctos
3. Ejecutar `python manage.py check`
4. Restaurar desde backup si es necesario

## ⚠️ **NOTAS IMPORTANTES:**

- **Base de datos**: Las migraciones pueden necesitar ajustes
- **URLs**: Algunas URLs pueden haber cambiado
- **Templates**: Todos usan ahora `base.html` como template base
- **Iconos**: FontAwesome 6.4.0 está correctamente configurado

## 🔧 **COMANDOS ÚTILES:**

```bash
# Verificar errores
python manage.py check

# Crear superusuario
python manage.py createsuperuser

# Ejecutar tests
python manage.py test

# Limpiar cache
python manage.py clear_cache
```

## 📞 **SOPORTE:**

Si encuentras problemas:
1. Revisa la carpeta `backup_original` para restaurar archivos
2. Verifica que todos los imports en archivos `.py` estén actualizados
3. Asegúrate de que las URLs en `Home/urls.py` coincidan con los nuevos nombres

¡Proyecto organizado y en español! 🎉
"""
    
    with open('GUIA_FINAL_REORGANIZACION.md', 'w', encoding='utf-8') as f:
        f.write(guia)
    
    print("✓ GUIA_FINAL_REORGANIZACION.md creado")
    print("\n📖 Revisa el archivo GUIA_FINAL_REORGANIZACION.md para instrucciones detalladas")

def main():
    """Función principal"""
    
    print("=" * 70)
    print("REORGANIZADOR COMPLETO DE PROYECTO DJANGO")
    print("Traducción al español + Mejoras de diseño + Organización")
    print("=" * 70)
    
    # Confirmación de seguridad
    print("\n⚠️  ADVERTENCIA: Este script hará cambios importantes en el proyecto.")
    print("Se creará un backup automáticamente antes de cualquier cambio.")
    
    respuesta = input("\n¿Deseas continuar con la reorganización? (s/n): ").lower()
    
    if respuesta != 's':
        print("Operación cancelada.")
        return
    
    print("\n🚀 Iniciando reorganización completa...")
    
    try:
        # Paso 1: Backup
        crear_backup()
        
        # Paso 2: Renombrar aplicaciones
        renombrar_aplicaciones()
        
        # Paso 3: Actualizar configuración
        actualizar_settings_py()
        actualizar_urls_py()
        
        # Paso 4: Actualizar imports en todo el proyecto
        actualizar_imports_en_todo_el_proyecto()
        
        # Paso 5: Actualizar templates
        actualizar_templates()
        
        # Paso 6: Mejorar CSS
        mejorar_css()
        
        # Paso 7: Crear guía final
        crear_archivo_guia_final()
        
        print("\n" + "=" * 70)
        print("✅ ¡REORGANIZACIÓN COMPLETADA CON ÉXITO!")
        print("=" * 70)
        
        print("\n🎉 El proyecto ha sido completamente reorganizado:")
        print("   • Aplicaciones renombradas al español")
        print("   • CSS mejorado con diseño moderno")
        print("   • Templates organizados y actualizados")
        print("   • Iconos de FontAwesome funcionando")
        print("   • Backup creado en carpeta 'backup_original'")
        
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: python manage.py makemigrations")
        print("   2. Ejecuta: python manage.py migrate")
        print("   3. Ejecuta: python manage.py runserver")
        print("   4. Prueba que todo funcione correctamente")
        
        print("\n🔧 Si hay problemas, revisa GUIA_FINAL_REORGANIZACION.md")
        
    except Exception as e:
        print(f"\n❌ Error durante la reorganización: {e}")
        print("Revisa el backup en la carpeta 'backup_original'")

if __name__ == "__main__":
    main()

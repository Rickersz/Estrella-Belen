# Guia de Produccion

## Variables obligatorias

1. Copia `.env.example` a `.env`.
2. Configura `DEBUG=False`.
3. Define una `SECRET_KEY` larga y privada.
4. Define `ALLOWED_HOSTS` con los dominios/IP reales.
5. Configura correo SMTP real para OTP, invitaciones y recuperacion de contrasena.
6. Configura reCAPTCHA real o desactivalo conscientemente con `RECAPTCHA_VERIFY_ENABLED=False`.

## Comandos basicos

```powershell
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic
python manage.py test
```

## Tareas programadas recomendadas

Ejecutar diariamente:

```powershell
python manage.py backup_system
python manage.py actualizar_pagos
```

`backup_system` crea un zip con `db.sqlite3` y `media/` dentro de `backups/`.

`actualizar_pagos` marca pagos vencidos y genera notificaciones de pagos proximos a vencer.

## Backup

Mantener copias fuera de la computadora principal. Como minimo:

- `db.sqlite3`
- `media/`
- `.env`

No subas backups ni `.env` a Git.

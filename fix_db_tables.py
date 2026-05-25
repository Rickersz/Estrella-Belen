import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Ver tablas actuales con home_auth
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'home_auth%'")
tablas = c.fetchall()
print("Tablas home_auth encontradas:", tablas)

# Renombrar tablas de home_auth a autenticacion
renombres = [
    ('home_auth_customuser', 'autenticacion_customuser'),
    ('home_auth_customuser_groups', 'autenticacion_customuser_groups'),
    ('home_auth_customuser_user_permissions', 'autenticacion_customuser_user_permissions'),
    ('home_auth_passwordresetrequest', 'autenticacion_passwordresetrequest'),
]

for viejo, nuevo in renombres:
    try:
        c.execute(f"ALTER TABLE {viejo} RENAME TO {nuevo}")
        print(f"✓ Renombrado: {viejo} → {nuevo}")
    except Exception as e:
        print(f"✗ Error con {viejo}: {e}")

conn.commit()
conn.close()
print("Listo.")

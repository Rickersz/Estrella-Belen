import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Actualizar nombre de app en tabla de migraciones
c.execute("UPDATE django_migrations SET app='autenticacion' WHERE app='home_auth'")
filas = c.rowcount
conn.commit()
conn.close()

print(f'Actualizado: {filas} filas en django_migrations')

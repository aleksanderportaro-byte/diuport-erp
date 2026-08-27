from core.models import Base, Company, User
from database import engine

print("Conectando con la base de datos de Neon...")

try:
  # Esto crea las tablas definidas en los modelos si aún no existen
  Base.metadata.create_all(bind=engine)
  print(
      "¡Conexión exitosa y tablas creadas correctamente en tu base de datos!"
  )
except Exception as e:
  print(f"Ocurrió un error al conectar o crear las tablas: {e}")
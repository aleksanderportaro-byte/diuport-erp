import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carga las variables de entorno
load_dotenv()

# URL de conexión a PostgreSQL (reemplaza esto con tu URL de Neon o Supabase cuando la tengas)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://usuario:contraseña@tu-servidor-postgres.com/tu_base",
)

# Configuración del motor de base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Función para obtener la sesión de base de datos en las peticiones
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()